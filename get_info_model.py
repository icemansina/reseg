import argparse
import collections
import cPickle as pkl

import matplotlib.pyplot as plt
import numpy
from tabulate import tabulate

from config_datasets import headers_datasets


def print_pkl_params(pkl_path, *args):
    """Loads a parameter pkl archive and prints the parameters

    Parameters
    ----------
    pkl_path : string
        The path of the .pkl parameter archive.
    *args : dict
        The arguments to print_params.
    """
    try:
        options = pkl.load(open(pkl_path, 'rb'))
    except IOError:
        print "Couldn't load " + pkl_path
        return 0
    save_plot_path = pkl_path.replace('models', 'plots').replace('.npz.pkl',
                                                                 '.pdf')
    return print_params(options, save_plot_path, *args)


def print_params(fp, save_plot_path='', print_commit_hash=False, plot=False,
                 print_history=False, print_best_class_accuracy=False,
                 ):
    """Prints the parameter of the model

    Parameters
    ----------
    fp : dict
        The dictionary of the model's parameters
    print_commit_hash : bool
        If True, the commit hash will be printed
    plot : bool
        If True, the error curves will be plotted
    print_history : bool
        If True the history of the accuracies will be printed
    """
    dataset = fp.get("dataset", "camvid")

    errs = fp.get('history_acc', None)
    if errs is None:
        errs = fp.get('history_errs', None)
    conf_matrices = numpy.array(fp['history_conf_matrix'])
    iou_indeces = numpy.array(fp['history_iou_index'])
    #nclasses = conf_matrices.shape[2] if len(conf_matrices) > 0 else -1
    # hack for nyu because now I don't have the time to think to something else
    # if dataset == 'nyu_depth':
    #     dataset = 'nyu_depth40' if nclasses == 41 else 'nyu_depth04'
    headers = headers_datasets.get(dataset, None)
    if headers is None:
        headers = [str(i) for i in range(0, fp['out_nfilters'][-1])]

    # they're already accuracies
    if len(errs):

        G_valid_idx = 3
        C_valid_idx = 4
        iou_valid_idx = 5

        min_valid = numpy.argmax(errs[:, iou_valid_idx])
        best = errs[min_valid]

        if 'cityscapes' in dataset:
            # for cityscapes we need to print the best iou index of the
            # validation set (we don't have the test)
            best_test_class_acc = numpy.round(iou_indeces[min_valid][1], 3)
        else:
            # in general we need to print the best accuracies of the test
            # given by the best validation model
            best_test_class_acc = numpy.round(
                numpy.diagonal(conf_matrices[min_valid][2]) /
                conf_matrices[min_valid][2].sum(axis=1), 3)

        if len(best_test_class_acc) > 0 and print_best_class_accuracy:
            best_per_class_accuracy = "|".join(
                best_test_class_acc.astype('str'))
        else:
            best_per_class_accuracy = ''

        # best_test_iou_indeces = numpy.round(iou_indeces[min_valid][2], 3)
        if len(best) == 2:
            error = (" ", round(best[0], 3), round(best[3], 3))
        else:

            if 'cityscapes' in dataset:
                # print the validation errors
                error = (round(best[0], 3), round(best[3], 3),
                         round(best[6], 3), round(best[4], 3),
                         round(best[5], 3))
            else:
                # print the test errors
                error = (round(best[0], 3), round(best[3], 3),
                         round(best[6], 3), round(best[7], 3),
                         round(best[8], 3))
    else:
        error = [' ', ' ', ' ', ' ', ' ']
        best_per_class_accuracy = ''

    if 'history_unoptimized_cost' in fp:
        huc = fp['history_unoptimized_cost']
    else:
        huc = None

    # GRU specific fp
    rnn_params = ' '
    if fp['RecurrentNet'].__name__ == 'GRULayer':
        rnn_params = ' '.join((fp['gru_resetgate'].__class__.__name__,
                               fp['gru_updategate'].__class__.__name__,
                               fp['gru_hidden_update'].__class__.__name__,
                               fp['gru_hid_init'].__class__.__name__,
                               str(fp['gru_hid_init'].val)))
    # LSTM specific fp
    if fp['RecurrentNet'].__name__ == 'LSTMLayer':

        rnn_params = ' '.join((fp['lstm_ingate'].__class__.__name__,
                               fp['lstm_forgetgate'].__class__.__name__,
                               fp['lstm_cell'].__class__.__name__,
                               fp['lstm_outgate'].__class__.__name__))
    # RNN specific fp
    if fp['RecurrentNet'].__name__ == 'RNNLayer':
        rnn_params = ' '.join((fp['rnn_W_hid_to_hid'].__class__.__name__,
                               fp['rnn_W_in_to_hid'].__class__.__name__,
                               fp['rnn_b'].__class__.__name__,
                               str(fp['rnn_b'].val)))

    print("{0}|{1}|{2}|{3}|{4}|{5}|{6}|{7}|{8}|{9}|{10}|{11}|{12}|{13}|"
          "{14}|{15}|{16}|{17}|{18}|{19}|{20}|{21}|{22}|{23}|{24}|{25}|"
          "{26}|{27}|{28}|{29}|{30}|{31}|{32}|{33}|{34}|{35}|{36}|{37}|"
          "{38}|{39}|{40}|{41}|{42}|{43}|{44}|{45}|{46}|{47}|{48}|{49}|"
          "{50}|{51}|{52}|"
          ).format(

        # Batch fp
        fp['batch_size'],

        # Dataset
        fp['color'],
        fp['color_space'],
        fp.get('use_depth', ' '),
        fp['shuffle'],

        # Pre_processing
        fp['preprocess_type'],
        str(fp['patch_size']) + ' ' +
        str(fp['max_patches']) if fp['preprocess_type'] in ('conv-zca',
                                                            'sub-lcn',
                                                            'subdiv-lcn',
                                                            'local_mean_sub')
        else ' ',
        fp['resize_images'],
        fp['resize_size'],

        # Data augmentation
        fp['do_random_flip'],
        fp['do_random_shift'],
        fp['do_random_invert_color'],

        # Input Conv layers
        fp['in_vgg_layer'] if 'in_vgg_layer' in fp else fp['in_nfilters'],
        fp['in_filters_size'] if isinstance(fp['in_nfilters'],
                                            collections.Iterable) else ' ',
        fp['in_filters_stride'] if isinstance(fp['in_nfilters'],
                                              collections.Iterable) else ' ',
        fp['in_W_init'].__class__.__name__ + ' , ' +
        fp['in_b_init'].__class__.__name__ + ' ' + str(fp['in_b_init'].val)
        if isinstance(fp['in_nfilters'], collections.Iterable) else ' ',
        fp['in_nonlinearity'].__name__
        if isinstance(fp['in_nfilters'], collections.Iterable) else ' ',


        # RNNs layers
        fp['dim_proj'],
        (fp['pwidth'], fp['pheight']),
        fp['stack_sublayers'],
        fp['RecurrentNet'].__name__,
        fp['nonlinearity'].__name__
        if fp['RecurrentNet'].__name__ in ('LSTMLayer', 'RNNLayer') else ' ',

        fp['hid_init'].__class__.__name__ + ' ' + str(fp['hid_init'].val),
        fp['grad_clipping'],
        # fp['precompute_input'],
        # fp['mask_input'],

        rnn_params,

        # Output upsampling layers
        fp['out_upsampling'],
        fp['out_nfilters'] if fp['out_upsampling'] == 'grad' else ' ',
        fp['out_filters_size'] if fp['out_upsampling'] == 'grad' else ' ',
        fp['out_filters_stride'] if fp['out_upsampling'] == 'grad' else ' ',
        fp['out_W_init'].__class__.__name__ + ', ' +
        fp['out_b_init'].__class__.__name__ + ' ' + str(fp['out_b_init'].val),
        fp['out_nonlinearity'].__name__ if fp['out_upsampling'] != 'linear'
        else ' ',

        # Prediction, Softmax
        fp['intermediate_pred'],
        fp['class_balance'],

        # Special layers
        fp['batch_norm'],
        fp['use_dropout'],
        fp['dropout_rate'] if fp['use_dropout'] else ' ',
        fp['use_dropout_x'],
        fp['dropout_x_rate'] if fp['use_dropout_x'] else ' ',


        # Optimization method
        fp['optimizer'].__name__,
        fp.get('learning_rate', ' '),
        ','.join((str(fp.get('momentum', ' ')),
                  str(fp.get('beta1', ' ')),
                  str(fp.get('beta2', ' ')),
                  str(fp.get('epsilon', ' '))
                  )),
        fp['weight_decay'],
        fp['weight_noise'],


        # Early stopping
        fp['patience'],
        fp['max_epochs'],
        fp['min_epochs'],
        len(errs),

        error[0],
        error[1],
        error[2],
        error[3],
        error[4],
        best_per_class_accuracy
    )

    if 'recseg_git_commit' in fp and print_commit_hash:
        print("Recseg commit: %s" % fp['recseg_git_commit'])
    if 'recseg_version' in fp and print_commit_hash:
        print("Recseg commit: %s" % fp['recseg_version'])
    if 'lasagne_version' in fp and print_commit_hash:
        print("Lasagne commit: %s" % fp['lasagne_version'])
    if 'theano_version' in fp and print_commit_hash:
        print("theano commit: %s" % fp['theano_version'])

    # plot error curves
    if plot:
        if errs.shape[1] == 2:
            newerrs = numpy.zeros([errs.shape[0], errs.shape[1]+1])
            newerrs[:, 1:3] = errs
            errs = newerrs

        # plt.subplot(2 if huc is not None else 1, 1, 1)

        # Plot Global Pixels % error
        plt.subplot(3, 1, 1)
        plt_range = range(len(errs))
        plt.plot(plt_range, 1 - errs[:, 0], label='train')
        plt.plot(plt_range, 1 - errs[:, 3], label='valid')
        plt.plot(plt_range, 1 - errs[:, 6], label='test')
        plt.grid(True)
        plt.ylim(-0.001, 1.1)
        plt.ylabel('Global Pixels error %')
        plt.legend(loc=1, fancybox=True, framealpha=0.1, fontsize='small')

        # plot Mean Pixels error %
        plt.subplot(3, 1, 2)
        plt_range = range(len(errs))
        plt.plot(plt_range, 1 - errs[:, 1], label='train')
        plt.plot(plt_range, 1 - errs[:, 4], label='valid')
        plt.plot(plt_range, 1 - errs[:, 7], label='test')
        plt.grid(True)
        plt.ylim(-0.001, 1.1)
        plt.ylabel('Avg Class error %')
        plt.legend(loc=1, fancybox=True, framealpha=0.1, fontsize='small')

        # Plot Mean IoU error %
        plt.subplot(3, 1, 3)
        plt_range = range(len(errs))
        plt.plot(plt_range, 1 - errs[:, 2], label='train')
        plt.plot(plt_range, 1 - errs[:, 5], label='valid')
        plt.plot(plt_range, 1 - errs[:, 8], label='test')
        plt.grid(True)
        plt.ylim(-0.001, 1.1)
        plt.ylabel('Avg IoU error %')
        plt.legend(loc=1, fancybox=True, framealpha=0.1, fontsize='small')

        if huc is not None:
            plt.subplot(2, 1, 2)
            scale = float(len(errs)) / len(huc)
            huc_range = [i * scale for i in range(len(huc))]
            plt.plot(huc_range, huc)
            plt.ylabel('Training cost')
            plt.grid(True)
        # plt.show()
        plt.savefig(save_plot_path, format="pdf")
    if print_history:
        for i, (e, c, iou) in enumerate(zip(errs, conf_matrices, iou_indeces)):

            (train_global_acc, train_mean_class_acc, train_mean_iou_index,
             valid_global_acc, valid_mean_class_acc, valid_mean_iou_index,
             test_global_acc, test_mean_class_acc, test_mean_iou_index) = e

            (train_conf_matrix, valid_conf_matrix, test_conf_matrix) = c
            # (train_iou_index, valid_iou_index, test_iou_index) = iou

            print ""
            print ""
            print ""
            print ""
            headers_acc = ["Global Accuracies",
                           "Mean Class Accuracies",
                           "Mean Intersection Over Union"]

            rows = list()
            rows.append(['Train ',
                        round(train_global_acc, 6),
                        round(train_mean_class_acc, 6),
                        round(train_mean_iou_index, 6)])

            rows.append(['Valid ',
                        round(valid_global_acc, 6),
                        round(valid_mean_class_acc, 6),
                        round(valid_mean_iou_index, 6)])

            rows.append(['Test ', round(test_global_acc, 6),
                         round(test_mean_class_acc, 6),
                         round(test_mean_iou_index, 6)])

            print(tabulate(rows, headers=headers_acc))

            train_conf_matrix_norm = (train_conf_matrix /
                                      train_conf_matrix.sum(axis=1))
            valid_conf_matrix_norm = (valid_conf_matrix /
                                      valid_conf_matrix.sum(axis=1))
            test_conf_matrix_norm = (test_conf_matrix /
                                     test_conf_matrix.sum(axis=1))

            class_acc = list()
            class_acc.append(numpy.concatenate([["Train"], numpy.round(
                numpy.diagonal(train_conf_matrix_norm), 3)]))
            class_acc.append(numpy.concatenate([["Valid"], numpy.round(
                numpy.diagonal(valid_conf_matrix_norm), 3)]))
            if len(test_conf_matrix) > 0:
                class_acc.append(numpy.concatenate([["Test"], numpy.round(
                    numpy.diagonal(test_conf_matrix_norm), 3)]))

            print(tabulate(class_acc, headers=headers))

            if dataset != "nyu_depth40":
                numpy.set_printoptions(precision=3)
                print ""
                print('Train Confusion matrix')
                print(tabulate(train_conf_matrix_norm, headers=headers))
                print ""
                print('Valid Confusion matrix')
                print(tabulate(valid_conf_matrix_norm, headers=headers))

                if len(test_conf_matrix_norm) > 0:
                    print ""
                    print('Test Confusion matrix')
                    print(tabulate(test_conf_matrix_norm, headers=headers))

            if i == -6:
                break

    return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Show the desired parameters of the network')
    parser.add_argument(
        'dataset',
        default='horses',
        help='The name of the esperiment.')
    parser.add_argument(
        'experiment',
        default='',
        nargs='?',
        help='The of the esperiment.')
    parser.add_argument(
        '--plot',
        '-p',
        action='store_true',
        help='Boolean. If set will plot the training curves')
    parser.add_argument(
        '--print-error-history',
        '-peh',
        action='store_true',
        help='Boolean. If set will print the value of the different '
             'metrics in every epoch')
    parser.add_argument(
        '--print_best_class_accuracy',
        '-pca',
        action='store_true',
        help='Boolean. If set will print the best per-class accuracy')
    parser.add_argument(
        '--print-commit-hash',
        '-ph',
        action='store_true',
        help='Boolean. If set will print the commit hash')
    parser.add_argument(
        '--model',
        default='model_recseg',
        help='The name of the model.')
    parser.add_argument(
        '--cycle',
        '-c',
        action='store_true',
        help='Boolean. If set will cycle through all the available '
             'saved models.')
    parser.add_argument(
        '--skip',
        '-s',
        nargs='*',
        type=int,
        default=[],
        help='List of experiment to skip from the cycle')

    args = parser.parse_args()
    if not args.cycle:
        print_pkl_params(args.dataset + '_models/' + args.model + '_' +
                         args.dataset + args.experiment + '.npz.pkl',
                         args.print_commit_hash, args.plot,
                         args.print_error_history,
                         args.print_best_class_accuracy)
    else:
        n = 0
        ok = 1
        while ok:
            n += 1
            if n in args.skip:
                print ''
                continue
            ok = print_pkl_params(args.dataset + '_models/' + args.model +
                                  '_' + args.dataset + str(n) + '.npz.pkl',
                                  args.print_commit_hash, args.plot,
                                  args.print_error_history,
                                  args.print_best_class_accuracy)
            if not ok:
                ok = print_pkl_params('/Tmp/visin/' + args.dataset +
                                      '_models/' + args.model + '_' +
                                      args.dataset + str(n) + '.npz.pkl',
                                      args.print_commit_hash, args.plot,
                                      args.print_error_history,
                                      args.print_best_class_accuracy)

        print('Printed models from 1 to {}').format(n-1)
