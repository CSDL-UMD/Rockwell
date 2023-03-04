#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  2 10:13:01 2021

@author: saumya
"""
import pandas as pd
from Surprise_partial_fit_svd.surprise_new.prediction_algorithms.matrix_factorization import SVD

import sys
sys.path.insert(1, '/home/saumya/Documents/USF/Project/ASD/recommendation_surprise/Surprise_partial_fit_svd') 
import Surprise_partial_fit_svd.surprise_new as reco_surprise

import Surprise_partial_fit_svd.surprise_new.prediction_algorithms.matrix_factorization

class mySVD(SVD):

    def sgd(self, trainset, partial=False):

        # OK, let's breathe. I've seen so many different implementation of this
        # algorithm that I just not sure anymore of what it should do. I've
        # implemented the version as described in the BellKor papers (RS
        # Handbook, etc.). Mymedialite also does it this way. In his post
        # however, Funk seems to implicitly say that the algo looks like this
        # (see reg below):
        # for f in range(n_factors):
        #       for _ in range(n_iter):
        #           for u, i, r in all_ratings:
        #               err = r_ui - <p[u, :f+1], q[i, :f+1]>
        #               update p[u, f]
        #               update q[i, f]
        # which is also the way https://github.com/aaw/IncrementalSVD.jl
        # implemented it.
        #
        # Funk: "Anyway, this will train one feature (aspect), and in
        # particular will find the most prominent feature remaining (the one
        # that will most reduce the error that's left over after previously
        # trained features have done their best). When it's as good as it's
        # going to get, shift it onto the pile of done features, and start a
        # new one. For efficiency's sake, cache the residuals (all 100 million
        # of them) so when you're training feature 72 you don't have to wait
        # for predictRating() to re-compute the contributions of the previous
        # 71 features. You will need 2 Gig of ram, a C compiler, and good
        # programming habits to do this."

        # A note on cythonization: I haven't dived into the details, but
        # accessing 2D arrays like pu using just one of the indices like pu[u]
        # is not efficient. That's why the old (cleaner) version can't be used
        # anymore, we need to compute the dot products by hand, and update
        # user and items factors by iterating over all factors...

        # user biases
        cdef np.ndarray[np.double_t] bu
        # item biases
        cdef np.ndarray[np.double_t] bi
        # user factors
        cdef np.ndarray[np.double_t, ndim=2] pu
        # item factors
        cdef np.ndarray[np.double_t, ndim=2] qi

        cdef int u, i, f
        cdef double r, err, dot, puf, qif
        cdef double global_mean = self.trainset.global_mean

        cdef double lr_bu = self.lr_bu
        cdef double lr_bi = self.lr_bi
        cdef double lr_pu = self.lr_pu
        cdef double lr_qi = self.lr_qi

        cdef double reg_bu = self.reg_bu
        cdef double reg_bi = self.reg_bi
        cdef double reg_pu = self.reg_pu
        cdef double reg_qi = self.reg_qi

        rng = get_rng(self.random_state)

        bu = np.zeros(trainset.n_users, np.double)
        bi = np.zeros(trainset.n_items, np.double)
        pu = rng.normal(self.init_mean, self.init_std_dev,
                        (trainset.n_users, self.n_factors))
        qi = rng.normal(self.init_mean, self.init_std_dev,
                        (trainset.n_items, self.n_factors))

        # if partial fit, start with previous model
        if partial and self.fitted:
            # print('in partial fit. values:')
            # print('self.bu:',self.bu)
            # print('self.bu0:',self.bu0)
            # print('self.bi:',self.bi)
            # print('self.bi0:',self.bi0)
            # print('self.pu:',self.pu)
            # print('self.qi:',self.qi)
            self.bu = self.bu0
            self.bi = self.bi0
            if (trainset._raw2inner_id_users != self.raw2inner_id_users
                    or trainset._raw2inner_id_items != self.raw2inner_id_items):
                # the trainset has changed, so we need to map the previous values  
                # of bu,pu,bi and qi to the appropriate indices
                # store previous values in appropriate locations in bu,pu,bi and qi
                for u in np.arange(trainset.n_users):
                    raw_u = trainset.to_raw_uid(u)
                    if raw_u in self.raw2inner_id_users.keys():
                        bu[u] = self.bu[self.raw2inner_id_users[raw_u]]
                        pu[u,:] = self.pu[self.raw2inner_id_users[raw_u],:]

                for i in np.arange(trainset.n_items):
                    raw_i = trainset.to_raw_iid(i)
                    if raw_i in self.raw2inner_id_items.keys():
                        bi[i] = self.bi[self.raw2inner_id_items[raw_i]]
                        qi[i,:] = self.qi[self.raw2inner_id_items[raw_i],:]
            else:   # 
                bu = self.bu
                bi = self.bi
                pu = self.pu
                qi = self.qi
        if not self.biased:
            global_mean = 0

        for current_epoch in range(self.n_epochs):
            if self.verbose:
                print("Processing epoch {}".format(current_epoch))
            for u, i, r in trainset.all_ratings():

                # compute current error
                dot = 0  # <q_i, p_u>
                for f in range(self.n_factors):
                    dot += qi[i, f] * pu[u, f]
                err = r - (global_mean + bu[u] + bi[i] + dot)

                # update biases
                if self.biased:
                    bu[u] += lr_bu * (err - reg_bu * bu[u])
                    bi[i] += lr_bi * (err - reg_bi * bi[i])

                # update factors
                for f in range(self.n_factors):
                    puf = pu[u, f]
                    qif = qi[i, f]
                    pu[u, f] += lr_pu * (err * qif - reg_pu * puf)
                    qi[i, f] += lr_qi * (err * puf - reg_qi * qif)

        self.bu = bu
        self.bu0 = bu
        self.bi = bi
        self.bi0 = bi
        self.pu = pu
        self.qi = qi
        self.fitted = True
        # store the trainset converters from raw2inner for users and items
        self.raw2inner_id_users = trainset._raw2inner_id_users
        self.raw2inner_id_items = trainset._raw2inner_id_items
        # print('fitted model. values:')
        # print('self.bu:',self.bu)
        # print('self.bi:',self.bi)
        # print('self.pu:',self.pu)
        # print('self.qi:',self.qi)

user = pd.read_csv('/home/saumya/Documents/USF/Project/popularity_bias/bookcrossing/BX-CSV-Dump/BX-Users.csv', sep=';', error_bad_lines=False, encoding="latin-1")
user.columns = ['userID', 'Location', 'Age']
rating = pd.read_csv('/home/saumya/Documents/USF/Project/popularity_bias/bookcrossing/BX-CSV-Dump/BX-Book-Ratings.csv', sep=';', error_bad_lines=False, encoding="latin-1")
rating.columns = ['userID', 'ISBN', 'bookRating']
df = pd.merge(user, rating, on='userID', how='inner')
df.drop(['Location', 'Age'], axis=1, inplace=True)
df.head()

min_book_ratings = 50
filter_books = df['ISBN'].value_counts() > min_book_ratings
filter_books = filter_books[filter_books].index.tolist()

min_user_ratings = 50
filter_users = df['userID'].value_counts() > min_user_ratings
filter_users = filter_users[filter_users].index.tolist()

df_new = df[(df['ISBN'].isin(filter_books)) & (df['userID'].isin(filter_users))]
print('The original data frame shape:\t{}'.format(df.shape))
print('The new data frame shape:\t{}'.format(df_new.shape))

reader = surprise.reader.Reader(rating_scale=(0, 9))
data = surprise.dataset.Dataset.load_from_df(df_new[['userID', 'ISBN', 'bookRating']], reader)

#trainset, testset = surprise.model_selection.split.train_test_split(data, test_size=0.25)

algo = surprise.SVD()
trainset = data.build_full_trainset()
algo.fit(trainset)