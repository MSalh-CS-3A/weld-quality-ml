"""Préparation reproductible de la Weld DB (Cambridge, Cool & Bhadeshia).

Conforme aux décisions de specs/spec.md (2026-10-08) :
- aucune conversion d'unité ; cellules suspectes rendues indisponibles (NaN) et tracées ;
- déduplication sur les 43 champs bruts hors ID (premier gardé, alias conservés) ;
- provenance par cellule (statut, bornes, opérateur de censure, annotation) ;
- groupes = séries dérivées des identifiants + liens créés par les doublons ;
- schémas par tâche (traction sans température Charpy) ;
- tout ce qui est appris (échelle, imputation, encodage) est ajusté DANS chaque pli
  via `make_preprocessor` — ne jamais réutiliser une matrice déjà transformée pour la CV.
"""
from __future__ import annotations

import hashlib
import re
import warnings

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.exceptions import ConvergenceWarning
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.linear_model import BayesianRidge

SEED = 42

# --------------------------------------------------------------------------- schéma brut
RAW_COLS = ['C', 'Si', 'Mn', 'S', 'P', 'Ni', 'Cr', 'Mo', 'V', 'Cu', 'Co', 'W',
            'O_ppm', 'Ti_ppm', 'N_ppm', 'Al_ppm', 'B_ppm', 'Nb_ppm', 'Sn_ppm', 'As_ppm', 'Sb_ppm',
            'current_A', 'voltage_V', 'ac_dc', 'polarity', 'heat_input_kJmm', 'interpass_C',
            'weld_type', 'pwht_temp_C', 'pwht_time_h',
            'yield_strength', 'uts', 'elongation', 'reduction_area', 'charpy_temp_C', 'charpy_J',
            'hardness', 'fatt50', 'prim_ferrite', 'ferrite_2nd_phase', 'acicular_ferrite',
            'martensite', 'ferrite_carbide', 'weld_id']
CAT_RAW = ['ac_dc', 'polarity', 'weld_type', 'weld_id']
NUM_RAW = [c for c in RAW_COLS if c not in CAT_RAW]
NONNEG = [c for c in NUM_RAW if c not in ('charpy_temp_C', 'fatt50')]   # températures d'essai peuvent être < 0
MICRO = ['prim_ferrite', 'ferrite_2nd_phase', 'acicular_ferrite', 'martensite', 'ferrite_carbide']

TENSILE = ['yield_strength', 'uts', 'elongation']        # tâches principales
COMPLEMENTARY = ['reduction_area']
ALL_TARGETS = TENSILE + COMPLEMENTARY + ['charpy_J']

# Jeux d'entrées (spec : A0 = cœur 11, candidat principal 13 = cœur + O/N, 16 = + Ni/Cr/Mo)
CORE_11 = ['C', 'Si', 'Mn', 'S', 'P', 'current_A', 'voltage_V', 'heat_input_kJmm',
           'interpass_C', 'pwht_temp_C', 'pwht_time_h']
FEATURE_SETS = {
    'A0_11': CORE_11,
    'A1_13': CORE_11 + ['O_ppm', 'N_ppm'],
    'A1b_16': CORE_11 + ['O_ppm', 'N_ppm', 'Ni', 'Cr', 'Mo'],
}
PRIMARY_SET = 'A1_13'
PROCESS_COL = 'weld_process'            # synonymes documentés seulement

# Synonymes documentés dans welddb.info (« ShMA = MMA », « SA = SMA »). Rien d'autre.
PROCESS_SYNONYMS = {'ShMA': 'MMA', 'SMA': 'SA'}


# --------------------------------------------------------------------------- lecture
def sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 16), b''):
            h.update(b)
    return h.hexdigest()


def read_raw(path) -> pd.DataFrame:
    raw = pd.read_csv(path, sep=r'\s+', header=None, names=RAW_COLS, dtype=str,
                      keep_default_na=False)
    assert raw.shape[1] == 44 and not raw.isna().any().any()
    raw.insert(0, 'raw_row_id', np.arange(len(raw)))          # indice brut 0-based, stable
    return raw


# --------------------------------------------------------------------------- provenance
_NUM = r'\d+(?:\.\d+)?'


def classify_token(col: str, tok: str) -> dict:
    """Statut lexical d'une cellule numérique brute. Aucune réinterprétation sémantique."""
    out = dict(status='exact', value=np.nan, lower=np.nan, upper=np.nan,
               censor_op='', annotation='')
    if tok == 'N':
        out['status'] = 'missing_N'
        return out
    if re.fullmatch(_NUM, tok) or re.fullmatch('-' + _NUM, tok):
        v = float(tok)
        out.update(value=v, lower=v, upper=v)
        return out
    m = re.fullmatch('<(' + _NUM + ')', tok)
    if m:
        out.update(status='censored_left', censor_op='<', lower=0.0, upper=float(m.group(1)))
        return out
    m = re.fullmatch('(' + _NUM + ')-(' + _NUM + ')', tok)
    if m:
        out.update(status='interval', lower=float(m.group(1)), upper=float(m.group(2)))
        return out
    if col == 'N_ppm':                       # ex. 67tot33res, 66totndres
        m = re.fullmatch(r'(\d+)tot(\d+|nd)res', tok)
        if m:
            out.update(status='annotated', annotation=f'tot={m.group(1)};res={m.group(2)}')
            return out
    if col == 'hardness':                    # ex. 158(Hv30), 459Hv10
        m = re.fullmatch(r'(\d+)\(?(Hv\d+)\)?', tok)
        if m:
            out.update(status='annotated', annotation=f'value={m.group(1)};protocol={m.group(2)}')
            return out
    out['status'] = 'unparsed'
    return out


def unit_review_flag(col: str, tok: str, info: dict) -> str:
    """Heuristiques NON résolues (spec 2026-10-05) : la cellule devient indisponible, rien n'est converti."""
    ppm_review = ('Ti_ppm', 'Al_ppm', 'Sn_ppm', 'As_ppm', 'Sb_ppm')
    if col in ppm_review and info['status'] == 'exact' and 0 < info['value'] < 1:
        return 'positive_below_1ppm'
    if col in ('Ti_ppm', 'Al_ppm') and tok == '<0.01':
        return 'censor_0.01_in_ppm_column'
    if col == 'V' and tok == '<5':
        return 'censor_5_in_wt%_column'
    return ''


def build_provenance(raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in NUM_RAW:
        for rid, tok in zip(raw.raw_row_id, raw[col]):
            info = classify_token(col, tok)
            rows.append(dict(raw_row_id=rid, column=col, raw_token=tok, **info,
                             review_flag=unit_review_flag(col, tok, info)))
    prov = pd.DataFrame(rows)
    assert (prov.status != 'unparsed').all(), prov[prov.status == 'unparsed'].head()
    return prov


def primary_value(prov: pd.DataFrame) -> pd.Series:
    """Représentation numérique principale (déterministe, sans apprentissage) :
    exact -> valeur ; censuré '<L' non signalé et >=0 -> L/2 (approximation) ;
    intervalle -> milieu (approximation) ; annoté, signalé ou N -> indisponible (NaN)."""
    v = prov['value'].copy()
    cens = (prov.status == 'censored_left') & (prov.review_flag == '')
    v[cens] = prov.loc[cens, 'upper'] / 2
    itv = prov.status == 'interval'
    v[itv] = (prov.loc[itv, 'lower'] + prov.loc[itv, 'upper']) / 2
    v[prov.review_flag != ''] = np.nan
    v[prov.status == 'annotated'] = np.nan
    return v


# --------------------------------------------------------------------------- doublons & groupes
def find_duplicates(raw: pd.DataFrame) -> pd.DataFrame:
    """Doublons exacts sur les 43 champs bruts hors ID ; le premier est conservé."""
    key = raw[[c for c in RAW_COLS if c != 'weld_id']].agg('\x1f'.join, axis=1)
    first = key.map(raw.groupby(key).raw_row_id.min())
    al = raw.loc[first != raw.raw_row_id, ['raw_row_id', 'weld_id']].copy()
    al['kept_raw_row_id'] = first[al.index].values
    al['kept_weld_id'] = raw.set_index('raw_row_id').loc[al.kept_raw_row_id, 'weld_id'].values
    return al.reset_index(drop=True)


# Familles explicites (non datées / lettres / rapports) et alias conservateurs (même auteurs+année,
# orthographe différente). Fusionner ne peut que réduire une fuite ; c'est une hypothèse documentée.
SERIES_FAMILIES = [
    (r'RR82011', 'RR82011'),                 # p9-RR82011 ... p36-RR82011 : un rapport
    (r'^EPRI-TR-101394', 'EPRI-TR-101394'),
    (r'^EvansLetter', 'EvansLetter'),        # EvansLetter, EvansLetterC, EvansLetterCo
]
# Variantes d'orthographe (mêmes auteurs + année, AUCUNE composition partagée constatée).
# Désactivé par défaut pour rester aligné sur la règle du projet (47 groupes) ; sensibilité possible.
NAME_VARIANTS = [
    (r'^Kocak.*TiN-1994', 'Kocak-TiN-1994'), # KocakPEv / KocakPREv
    (r'^Gar?&K-1975', 'Gar&K-1975'),         # Ga&K / Gar&K
]
MERGE_NAME_VARIANTS = False


def series_of(weld_id: str) -> tuple[str, str]:
    fams = SERIES_FAMILIES + (NAME_VARIANTS if MERGE_NAME_VARIANTS else [])
    for pat, fam in fams:
        if re.search(pat, weld_id):
            return fam, 'explicit_family'
    m = re.match(r'^(.*?(?:19|20)\d\d)', weld_id)
    if m:
        return m.group(1), 'prefix_year'
    if '-' in weld_id:
        return weld_id.split('-')[0], 'undated_prefix'
    return weld_id, 'exact_id_fallback'


def build_groups(raw: pd.DataFrame, aliases: pd.DataFrame) -> pd.DataFrame:
    s = raw.weld_id.map(series_of)
    out = pd.DataFrame({'raw_row_id': raw.raw_row_id, 'weld_id': raw.weld_id,
                        'series': s.str[0], 'series_rule': s.str[1]})
    # union-find : un doublon relie la série de l'alias à celle de l'enregistrement conservé
    parent = {x: x for x in out.series.unique()}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    ser = out.set_index('raw_row_id').series
    for a, k in zip(aliases.raw_row_id, aliases.kept_raw_row_id):
        ra, rk = find(ser[a]), find(ser[k])
        if ra != rk:
            parent[max(ra, rk)] = min(ra, rk)
    out['group'] = out.series.map(find)
    return out


# --------------------------------------------------------------------------- table maître
def build_master(path):
    raw = read_raw(path)
    prov = build_provenance(raw)
    prov['primary_value'] = primary_value(prov)
    aliases = find_duplicates(raw)
    groups = build_groups(raw, aliases)

    num = prov.pivot(index='raw_row_id', columns='column', values='primary_value')[NUM_RAW]
    m = raw[['raw_row_id', 'weld_id']].set_index('raw_row_id').join(num)
    m = m.join(groups.set_index('raw_row_id')[['series', 'series_rule', 'group']])

    # catégories : codes d'origine conservés ; synonymes documentés seulement
    m['weld_type_raw'] = raw.set_index('raw_row_id').weld_type
    m[PROCESS_COL] = m.weld_type_raw.replace(PROCESS_SYNONYMS)
    m['ac_dc_raw'] = raw.set_index('raw_row_id').ac_dc.replace('N', 'missing')
    m['polarity_raw'] = raw.set_index('raw_row_id').polarity.replace('N', 'missing')
    m['flag_ac_with_polarity'] = (m.ac_dc_raw == 'AC') & m.polarity_raw.isin(['+', '-'])
    m['flag_polarity_without_current_type'] = (m.ac_dc_raw == 'missing') & m.polarity_raw.isin(['+', '-'])

    # annotations conservées hors matrice principale
    pv = prov.set_index(['raw_row_id', 'column'])
    m['N_annotation'] = pv.xs('N_ppm', level='column').annotation
    hd = pv.xs('hardness', level='column')
    m['hardness_value'] = np.where(hd.status == 'exact', hd.value,
                                   hd.annotation.str.extract(r'value=(\d+)')[0].astype(float))
    m['hardness_protocol'] = np.where(hd.status == 'exact', 'unspecified',
                                      hd.annotation.str.extract(r'protocol=(Hv\d+)')[0].fillna('missing'))
    m.loc[hd.status == 'missing_N', 'hardness_protocol'] = 'missing'
    m = m.drop(columns='hardness')
    m['micro_sum'] = m[MICRO].sum(axis=1, min_count=5)
    m['flag_micro_sum_not_100'] = m.micro_sum.notna() & (m.micro_sum.sub(100).abs() > 0.5)
    m['flag_pwht_missing'] = m.pwht_temp_C.isna() | m.pwht_time_h.isna()

    # déduplication
    m['is_duplicate_excess'] = m.index.isin(aliases.raw_row_id)
    alt = aliases.groupby('kept_raw_row_id').weld_id.agg(';'.join)
    m['alternate_ids'] = m.index.map(alt).fillna('')

    # éligibilité
    for f, cols in FEATURE_SETS.items():
        m[f'n_unavail_{f}'] = m[cols].isna().sum(axis=1)
    m['in_strict13'] = ~m.is_duplicate_excess & (m[f'n_unavail_{PRIMARY_SET}'] <= 2)
    for t in ALL_TARGETS:
        m[f'has_{t}'] = m[t].notna()
    m['is_unlabeled_all'] = ~m[[f'has_{t}' for t in ALL_TARGETS]].any(axis=1)
    return raw, prov, aliases, groups, m.reset_index()


# --------------------------------------------------------------------------- Charpy
def charpy_protocol_table(m: pd.DataFrame) -> pd.DataFrame:
    """Indices par série — candidats seulement, aucune affectation de protocole adoptée."""
    c = m[~m.is_duplicate_excess & m.charpy_J.notna()]
    def agg(g):
        e = g.charpy_J
        return pd.Series(dict(
            n=len(g), n_distinct_energy=e.nunique(), n_distinct_temp=g.charpy_temp_C.nunique(),
            share_100J=(e == 100).mean().round(3), share_28J=(e == 28).mean().round(3),
            other_energies=int((~e.isin([100, 28])).sum()),
        ))
    t = c.groupby('group').apply(agg, include_groups=False)
    # Signature de protocole par série (pas par valeur d'énergie isolée) :
    # énergie (quasi) constante sur de nombreuses températures = critère à énergie fixée probable.
    r = t.n_distinct_energy / t.n
    t['signature'] = np.select(
        [(r <= 0.1) & (t.n_distinct_temp > t.n_distinct_energy), r >= 0.5],
        ['fixed_energy_varying_T', 'varying_E'], 'mixed_unresolved')
    t['candidate_task'] = t.signature.map({'fixed_energy_varying_T': 'T(E_fixed) — ex. T100J/T28J',
                                           'varying_E': 'E(T)', 'mixed_unresolved': 'none (review)'})
    t['status'] = 'hypothesis — verify against the source publication'
    return t.sort_values('n', ascending=False)


# --------------------------------------------------------------------------- folds
def assign_folds(m: pd.DataFrame, n_outer=5, n_inner=3) -> pd.DataFrame:
    """Plis externes par groupe (GroupKFold déterministe, sans shuffle), communs à toutes
    les cibles ; plis internes par groupe à l'intérieur de chaque entraînement externe."""
    from sklearn.model_selection import GroupKFold
    d = m.loc[~m.is_duplicate_excess, ['raw_row_id', 'group']].reset_index(drop=True)
    d['outer_fold'] = -1
    for k, (_, te) in enumerate(GroupKFold(n_splits=n_outer).split(d, groups=d.group)):
        d.loc[te, 'outer_fold'] = k
    for k in range(n_outer):
        tr = d.index[d.outer_fold != k]
        col = f'inner_fold_when_outer{k}'
        d[col] = -1
        n_g = d.loc[tr, 'group'].nunique()
        for j, (_, te) in enumerate(GroupKFold(n_splits=min(n_inner, n_g)).split(tr, groups=d.loc[tr, 'group'])):
            d.loc[tr[te], col] = j
    return d


# --------------------------------------------------------------------------- preprocessing appris
class FoldPreprocessor(BaseEstimator, TransformerMixin):
    """À ajuster sur les lignes d'entraînement d'un pli uniquement.

    1. standardisation des entrées numériques (moyenne/écart-type du train, NaN ignorés) ;
    2. one-hot du procédé (catégories du train ; inconnue -> vecteur nul) ;
    3. imputation : 'iterative' (IterativeImputer/BayesianRidge, init médiane, ordre ascendant,
       max_iter=100, tol=1e-3, random_state=42, bornes physiques >= 0) ou 'median' ;
    4. PWHT : un couple (température, durée) imputé est projeté sur le couple réel du train
       le plus proche (distance en écarts-types du train), en respectant une valeur observée.
    Une colonne entièrement absente du train est refusée plutôt que fabriquée.
    Sortie : entrées standardisées + indicatrices du procédé. Les cibles n'entrent jamais ici.
    """

    def __init__(self, num_cols, cat_col=PROCESS_COL, method='iterative', max_iter=100,
                 tol=1e-3, random_state=SEED):
        self.num_cols, self.cat_col, self.method = num_cols, cat_col, method
        self.max_iter, self.tol, self.random_state = max_iter, tol, random_state

    def _encode(self, X):
        Z = (X[self.num_cols].to_numpy(float) - self.mu_) / self.sd_
        C = np.stack([(X[self.cat_col] == c).to_numpy(float) for c in self.cats_], axis=1) \
            if self.cat_col else np.empty((len(X), 0))
        return np.hstack([Z, C])

    def fit(self, X, y=None):
        Xn = X[self.num_cols].astype(float)
        empty = Xn.columns[Xn.notna().sum() == 0].tolist()
        if empty:
            raise ValueError(f'Colonnes entièrement absentes du train : {empty}')
        self.mu_ = Xn.mean().to_numpy()
        self.sd_ = Xn.std(ddof=0).replace(0, 1).to_numpy()
        self.cats_ = sorted(X[self.cat_col].dropna().unique()) if self.cat_col else []
        Z = self._encode(X)
        lo = np.full(Z.shape[1], -np.inf)
        for i, c in enumerate(self.num_cols):
            if c in NONNEG:
                lo[i] = (0 - self.mu_[i]) / self.sd_[i]
        if self.method == 'iterative':
            self.imp_ = IterativeImputer(estimator=BayesianRidge(), initial_strategy='median',
                                         imputation_order='ascending', max_iter=self.max_iter,
                                         tol=self.tol, random_state=self.random_state,
                                         skip_complete=False, min_value=lo, keep_empty_features=True)
        elif self.method == 'median':
            self.imp_ = SimpleImputer(strategy='median', keep_empty_features=True)
        else:
            raise ValueError(self.method)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', ConvergenceWarning)
            self.imp_.fit(Z)
        self.converged_ = (self.method != 'iterative') or (self.imp_.n_iter_ < self.max_iter)
        self.n_iter_ = getattr(self.imp_, 'n_iter_', 0)
        # couples PWHT réels du train
        self.pw_idx_ = [self.num_cols.index(c) for c in ('pwht_temp_C', 'pwht_time_h')
                        if c in self.num_cols]
        if len(self.pw_idx_) == 2:
            P = Z[:, self.pw_idx_]
            self.pw_pairs_ = np.unique(P[~np.isnan(P).any(axis=1)], axis=0)
        return self

    def transform(self, X):
        Z = self._encode(X)
        miss = np.isnan(Z)
        out = self.imp_.transform(Z)
        if len(self.pw_idx_) == 2 and len(self.pw_pairs_):
            i, j = self.pw_idx_
            for r in np.where(miss[:, i] | miss[:, j])[0]:
                cand = self.pw_pairs_
                if not miss[r, i]:   # température observée : couples compatibles seulement
                    ok = np.isclose(cand[:, 0], Z[r, i]); cand = cand[ok] if ok.any() else cand
                if not miss[r, j]:
                    ok = np.isclose(cand[:, 1], Z[r, j]); cand = cand[ok] if ok.any() else cand
                best = cand[np.argmin(((cand - out[r, [i, j]]) ** 2).sum(axis=1))]
                out[r, i] = Z[r, i] if not miss[r, i] else best[0]
                out[r, j] = Z[r, j] if not miss[r, j] else best[1]
        return out

    def get_feature_names_out(self, input_features=None):
        return np.array([str(c) for c in self.num_cols] + [f'{self.cat_col}={c}' for c in self.cats_], dtype=object)


def task_schema(task: str, feature_set: str = PRIMARY_SET) -> dict:
    """Entrées autorisées par tâche. La température Charpy n'est une entrée que pour E(T)."""
    num = list(FEATURE_SETS[feature_set])
    if task in TENSILE + COMPLEMENTARY:
        return dict(target=task, num=num, cat=PROCESS_COL, status='adopted')
    if task == 'charpy_E_of_T':
        return dict(target='charpy_J', num=num + ['charpy_temp_C'], cat=PROCESS_COL,
                    status='conditional — protocol classification pending')
    if task in ('T100J', 'T28J'):
        return dict(target='charpy_temp_C', num=num, cat=PROCESS_COL,
                    status='conditional — protocol classification pending')
    raise ValueError(task)
