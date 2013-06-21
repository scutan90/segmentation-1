import numpy as np

from sklearn.utils import shuffle
#from sklearn.grid_search import GridSearchCV

from pystruct.models import EdgeFeatureGraphCRF, LatentNodeCRF
from pystruct import learners
from pystruct.utils import SaveLogger
#from pystruct.models.latent_node_crf import kmeans_init

from datasets.pascal import PascalSegmentation
from pascal_helpers import load_pascal
from latent_crf_experiments.utils import discard_void, add_edges
                                          #add_edge_features)
from latent_crf_experiments.hierarchical_segmentation import \
    make_hierarchical_data

from IPython.core.debugger import Tracer
tracer = Tracer()


def svm_on_segments(C=.1, learning_rate=.001, subgradient=False):
    ds = PascalSegmentation()
    # load and prepare data
    lateral = True
    latent = True
    data_train = load_pascal("train1")
    data_train = add_edges(data_train)
    #if lateral:
        #data_train = add_edge_features(ds, data_train)
    X_org_ = data_train.X
    data_train = make_hierarchical_data(ds, data_train, lateral=lateral,
                                        latent=latent, latent_lateral=False)
    data_train = discard_void(ds, data_train)
    X_, Y_ = data_train.X, data_train.Y
    # remove edges
    if not lateral:
        X_org_ = [(x[0], np.zeros((0, 2), dtype=np.int)) for x in X_org_]

    n_states = 21
    class_weights = 1. / np.bincount(np.hstack(Y_))
    class_weights *= 21. / np.sum(class_weights)
    experiment_name = ("latent_20_features_C%f" % C)
    logger = SaveLogger(experiment_name + ".pickle", save_every=10)
    if latent:
        model = LatentNodeCRF(n_labels=n_states,
                              n_features=data_train.X[0][0].shape[1],
                              n_hidden_states=5, inference_method='qpbo' if
                              lateral else 'dai', class_weight=class_weights,
                              latent_node_features=False)
        if subgradient:
            ssvm = learners.LatentSubgradientSSVM(
                model, C=C, verbose=1, show_loss_every=10, logger=logger,
                n_jobs=-1, learning_rate=learning_rate, decay_exponent=1,
                momentum=0., max_iter=100000)
        else:
            latent_logger = SaveLogger("lssvm_" + experiment_name +
                                       "_%d.pickle", save_every=1)
            base_ssvm = learners.OneSlackSSVM(
                model, verbose=2, C=C, max_iter=100000, n_jobs=-1, tol=0.001,
                show_loss_every=200, inference_cache=50, logger=logger,
                cache_tol='auto', inactive_threshold=1e-5, break_on_bad=False,
                switch_to_ad3=True)
            ssvm = learners.LatentSSVM(base_ssvm, logger=latent_logger)
        warm_start = False
        if warm_start:
            ssvm = logger.load()
            ssvm.logger = SaveLogger(experiment_name + "_retrain.pickle",
                                     save_every=10)
            ssvm.max_iter = 100000
            ssvm.learning_rate = 0.00001
            ssvm.momentum = 0
    else:
        #model = GraphCRF(n_states=n_states,
                         #n_features=data_train.X[0][0].shape[1],
                         #inference_method='qpbo' if lateral else 'dai',
                         #class_weight=class_weights)
        model = EdgeFeatureGraphCRF(n_states=n_states,
                                    n_features=data_train.X[0][0].shape[1],
                                    inference_method='qpbo' if lateral else
                                    'dai', class_weight=class_weights,
                                    n_edge_features=4,
                                    symmetric_edge_features=[0, 1],
                                    antisymmetric_edge_features=[2])
        ssvm = learners.OneSlackSSVM(
            model, verbose=2, C=C, max_iter=100000, n_jobs=-1,
            tol=0.0001, show_loss_every=200, inference_cache=50, logger=logger,
            cache_tol='auto', inactive_threshold=1e-5, break_on_bad=False)

    #ssvm = logger.load()

    X_, Y_ = shuffle(X_, Y_)
    #ssvm.fit(data_train.X, data_train.Y)
    ssvm.fit(X_, Y_)
    #H_init = [np.hstack([y, np.random.randint(21, 26)]) for y in Y_]
    #ssvm.fit(X_, Y_, H_init=H_init)
    print("fit finished!")


#def plot_init():
    #data = load_pascal("train")
    #data = make_hierarchical_data(data, lateral=False, latent=True)
    ##X, Y = discard_void(data.X, data.Y, 21)
    ##data.X, data.Y = X, Y
    #H = kmeans_init(data.X, data.Y, n_labels=22, n_hidden_states=22)
    #plot_results_hierarchy(data, H)


#def plot_results():
    #data = load_pascal("val")
    #data = make_hierarchical_data(data, lateral=False, latent=True)
    #logger = SaveLogger("test_latent_2.0001.pickle", save_every=100)
    #ssvm = logger.load()
    #plot_results_hierarchy(data, ssvm.predict(data.X),
                           #folder="latent_results_val_50_states_no_lateral")


if __name__ == "__main__":
    #for C in 10. ** np.arange(-5, 2):
    #for lr in 10. ** np.arange(-3, 2)[::-1]:
        #svm_on_segments(C=.01, learning_rate=lr)
    #svm_on_segments(C=.01, learning_rate=0.1)
    svm_on_segments(C=.01, subgradient=False)
    #plot_init()
    #plot_results()
