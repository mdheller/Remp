
from libcpp.vector cimport vector
from libcpp.map cimport map as omap

'''
cdef extern from "inverted_index_cy.h" nogil:
    cdef cppclass InvertedIndexCy nogil:
        InvertedIndexCy()
        InvertedIndexCy(omap[int, vector[int]]&, vector[int]&)
        void set_fields(omap[int, vector[int]]&, vector[int]&)
        void build_prefix_index(vector[vector[int]]&, int, double)
        omap[int, vector[int]] index
        vector[int] size_vector
'''

cdef class InvertedIndexCy:
    cdef void set_fields(self, omap[int, vector[int]]&, vector[int]&)
    cdef void build_prefix_index(self, vector[vector[int]]&, int, double)
    cdef omap[int, vector[int]] index
    cdef vector[int] size_vector
