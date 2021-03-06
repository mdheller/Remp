import pandas as pd
from .util import suffix
import py_stringmatching as sm
from remp import string_matching

tokenizer = sm.QgramTokenizer(qval=2, return_set=True)
jaccard = sm.Jaccard()


def similarity_func_default(string1, string2):
    return jaccard.get_sim_score(tokenizer.tokenize(string1),
                                 tokenizer.tokenize(string2))


def construct_similarity_list(left_triples, right_triples, entity_candidates,
                              aligned_attributes=None, similarity_func=None):
    if aligned_attributes is None:
        shared_attributes = set(left_triples['a'].unique())
        shared_attributes &= set(right_triples['a'].unique())
        shared_attributes = list(shared_attributes)
        aligned_attributes = pd.DataFrame({'a1': shared_attributes,
                                           'a2': shared_attributes})
    if 'attr_id' not in aligned_attributes:
        aligned_attributes['attr_id'] = aligned_attributes.index
    paired = pd.merge(entity_candidates, suffix(left_triples, '1'))
    paired = pd.merge(paired, aligned_attributes)
    paired = pd.merge(paired, suffix(right_triples, '2'))
    import time
    start = time.time()
    if similarity_func is None:
        paired['sim'] = string_matching.array_qgram_jaccard_2(
                            paired.v1.apply(str).values,
                            paired.v2.apply(str).values)
    else:
        paired['sim'] = paired.apply(lambda tu: similarity_func(
                                                tu['v1'], tu['v2']), axis=1)
    return paired


def construct_similarity_vector(left_triples, right_triples, entity_candidates,
                                aligned_attributes=None, similarity_func=None):
    paired = construct_similarity_list(
        left_triples, right_triples, entity_candidates, aligned_attributes,
        similarity_func)

    df = pd.pivot_table(paired, values=['sim'], index=['s1', 's2'],
                        columns='attr_id', aggfunc='max')
    return df


def construct_similarity_vector_from_tuples(
        left_tuples, right_tuples, entity_candidates,
        aligned_attributes=None, similarity_func=None):
    if aligned_attributes is None:
        shared_attributes = list(set(left_tuples.columns) &
                                 set(right_tuples.columns) - {'s'})
        aligned_attributes = pd.DataFrame(
            {'a1': shared_attributes, 'a2': shared_attributes})
    paired = pd.merge(entity_candidates, suffix(left_tuples, '1'))
    paired = pd.merge(paired, suffix(right_tuples, '2'))
    vector = {}
    for attr_pair in aligned_attributes.itertuples():
        (a1, a2) = (attr_pair.a1, attr_pair.a2)
        a1 += '1'
        a2 += '2'
        col_name = 'sim_%s_%s' % (a1, a2)
        if similarity_func is None:
            vector[col_name] = string_matching.array_qgram_jaccard_2(
                paired[a1].values, paired[a2].values)
        else:
            vector[col_name] = paired.apply(
                lambda tu: similarity_func(str(tu[a1]), str(tu[a2])), axis=1)
    paired = paired[['s1', 's2']]
    for k, v in vector.items():
        paired[k] = v
    return paired.set_index(['s1', 's2'])


def compute_extended_jaccard(graph, s='s', o='o', r='r'):
    o_n = graph.groupby(by=[s + '1', s + '2', r]).agg(
        {o + '1': 'nunique', o + '2': 'nunique'}
        ).sum(1).rename('o_n').reset_index()
    ej = graph[graph[o + 'p'] >= 0.9].groupby(by=[s + '1', s + '2', r]).agg(
        {o + '1': 'nunique', o + '2': 'nunique', r: 'count'}
        )
    ej = ej.rename(columns={r: 's'}).reset_index()
    ej = pd.merge(ej, o_n)
    ej['ej'] = ej['s'] / (ej['s'] + ej['o_n'] - ej[o + '1'] - ej[o + '2'])
    return ej[[s + '1', s + '2', r, 'ej']]

def prior_probabilities(dataset, M_pruned):
    import unidecode
    import tempfile
    cache_base_dir = tempfile.mkdtemp('remp')
    (l1, l2) = dataset.label
    labels_1 = dataset.attributes_1[
        dataset.attributes_1['a'] == l1][['s', 'a', 'v']]
    labels_2 = dataset.attributes_2[
        dataset.attributes_2['a'] == l2][['s', 'a', 'v']]

    labels_1['v'] = labels_1['v'].apply(
        str).apply(unidecode.unidecode).str.lower()
    labels_2['v'] = labels_2['v'].apply(
        str).apply(unidecode.unidecode).str.lower()
    
    return construct_similarity_list(labels_1, labels_2, M_pruned)[['s1', 's2', 'sim']]