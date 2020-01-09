import numpy as np
from .data import Data
import matplotlib.pyplot as plt

class DataSet:
    def __init__(self, *args):
        """
        DataSet is a class that holds multiple Data objects as channels.

        Args:
            *args (mogptk.data.Data, mogptk.dataset.DataSet, list, dict): Accepts multiple arguments, each of which should be either a DataSet or Data object, a list of Data objects or a dictionary of Data objects. Each Data object will be added to the list of channels. In case of a dictionary, the key will set the name of the Data object. If a DataSet is passed, its channels will be added.

        Examples:
            >>> dataset = mogptk.DataSet(channel_a, channel_b, channel_c)
        """

        self.channels = []
        for arg in args:
            self.append(arg)

    def __iter__(self):
        return self.channels.__iter__()

    def __len__(self):
        return len(self.channels)

    def __getitem__(self, key):
        if isinstance(key, str):
            return self.channels[self.get_names().index(key)]
        return self.channels[key]

    def append(self, arg):
        """
        Append channel(s) to DataSet.
        
        Args:
            arg (mogptk.data.Data, mogptk.dataset.DataSet, list, dict): Argument can be either a DataSet or Data object, a list of Data objects or a dictionary of Data objects. Each Data object will be added to the list of channels. In case of a dictionary, the key will set the name of the Data object. If a DataSet is passed, its channels will be added.

        Examples:
            >>> dataset.append(mogptk.LoadFunction(lambda x: np.sin(5*x[:,0]), n=200, start=0.0, end=4.0, name='A'))
        """
        if isinstance(arg, Data):
            self.channels.append(arg)
        elif isinstance(arg, DataSet):
            for val in arg.channels:
                self.channels.append(val)
        elif isinstance(arg, list) and all(isinstance(val, Data) for val in arg):
            for val in arg:
                self.channels.append(val)
        elif isinstance(arg, dict) and all(isinstance(val, Data) for val in arg.values()):
            for key, val in arg.items():
                val.name = key
                self.channels.append(val)
        else:
            raise Exception("unknown data type %s in append to DataSet" % (type(arg)))
        return self

    def get_input_dims(self):
        """
        Return the input dimensions per channel.

        Returns:
            list: List of input dimensions per channel.

        Examples:
            >>> dataset.get_input_dims()
            [2, 1]
        """
        return [channel.get_input_dims() for channel in self.channels]

    def get_output_dims(self):
        """
        Return the output dimensions of the dataset, i.e. the number of channels.

        Returns:
            int: Output dimensions.

        Examples:
            >>> dataset.get_output_dims()
            4
        """
        return len(self.channels)

    def get_names(self):
        """
        Return the names of the channels.

        Returns:
            list: List of names.

        Examples:
            >>> dataset.get_names()
            ['A', 'B', 'C']
        """
        return [channel.get_name() for channel in self.channels]

    def get(self, index):
        """
        Return Data object given a channel index or name.

        Args:
            index (int, str): Index or name of the channel.

        Returns:
            mogptk.data.Data: Channel data.

        Examples:
            >>> channel = dataset.get('A')
        """
        if isinstance(index, int):
            if index < len(self.channels):
                return self.channels[index]
        elif isinstance(index, str):
            for channel in self.channels:
                if channel.name == index:
                    return channel
        raise ValueError("channel '%d' does not exist in DataSet" % (index))
    
    def get_data(self):
        """
        Returns observations.

        Returns:
            list: X data of shape (n,input_dims) per channel.
            list: Y data of shape (n,) per channel.

        Examples:
            >>> x, y = dataset.get_data()
        """
        return [channel.get_data()[0] for channel in self.channels], [channel.get_data()[1] for channel in self.channels]
    
    def get_all(self):
        """
        Returns all observations (including removed observations).

        Returns:
            list: X data of shape (n,input_dims) per channel.
            list: Y data of shape (n,) per channel.

        Examples:
            >>> x, y = dataset.get_all()
        """
        return [channel.get_all()[0] for channel in self.channels], [channel.get_all()[1] for channel in self.channels]

    def get_removed(self):
        """
        Returns the removed observations.

        Returns:
            list: X data of shape (n,input_dims) per channel.
            list: Y data of shape (n,) per channel.

        Examples:
            >>> x, y = dataset.get_removed()
        """
        return [channel.get_removed()[0] for channel in self.channels], [channel.get_removed()[1] for channel in self.channels]
    
    def get_pred(self, name, sigma=2):
        """
        Returns the prediction of a given name with a normal variance of sigma.

        Args:
            name (str): Name of the prediction, equals the name of the model that made the prediction.
            sigma (float): The uncertainty interval calculated at mean-sigma*var and mean+sigma*var. Defaults to 2,

        Returns:
            list: X prediction of shape (n,input_dims) per channel.
            list: Y mean prediction of shape (n,) per channel.
            list: Y lower prediction of uncertainty interval of shape (n,) per channel.
            list: Y upper prediction of uncertainty interval of shape (n,) per channel.

        Examples:
            >>> x, y_mean, y_var_lower, y_var_upper = dataset.get_pred('MOSM', sigma=1)
        """
        x = []
        mu = []
        lower = []
        upper = []
        for channel in self.channels:
            channel_x, channel_mu, channel_lower, channel_upper = channel.get_pred(name, sigma)
            x.append(channel_x)
            mu.append(channel_mu)
            lower.append(channel_lower)
            upper.append(channel_upper)
        return x, mu, lower, upper

    def set_pred(self, x):
        """
        Set the prediction range per channel.

        Args:
            x (list, dict): Array of shape (n,) or (n,input_dims) per channel with prediction X values. If a dictionary is passed, the index is the channel index or name.

        Examples:
            >>> dataset.set_pred([[5.0, 5.5, 6.0, 6.5, 7.0], [0.1, 0.2, 0.3]])
            >>> dataset.set_pred({'A': [5.0, 5.5, 6.0, 6.5, 7.0], 'B': [0.1, 0.2, 0.3]})
        """
        if isinstance(x, list):
            if len(x) != len(self.channels):
                raise ValueError("prediction x expected to be a list of shape (output_dims,n)")

            for i, channel in enumerate(self.channels):
                channel.set_pred(x[i])
        elif isinstance(x, dict):
            for name in x:
                self.get(name).set_pred(x[name])
        else:
            for i, channel in enumerate(self.channels):
                channel.set_pred(x)

    def set_pred_range(self, start, end, n=None, step=None):
        """
        Set the prediction range per channel. Inputs should be lists of shape (input_dims,) for each channel or dicts where the keys are the channel indices.

        Args:
            start (list, dict): Start values for prediction range per channel.
            end (list, dict): End values for prediction range per channel.
            n (list, dict, optional): Number of points for prediction range per channel.
            step (list, dict, optional): Step size for prediction range per channel.

        Examples:
            >>> dataset.set_pred_range([2, 3], [5, 6], [4, None], [None, 0.5])
            >>> dataset.set_pred_range(0.0, 5.0, n=200) # the same for each channel
        """
        if not isinstance(start, (list, dict)):
            start = [start] * self.get_output_dims()
        elif isinstance(start, dict):
            start = [start[name] for name in self.get_names()]
        if not isinstance(end, (list, dict)):
            end = [end] * self.get_output_dims()
        elif isinstance(end, dict):
            end = [end[name] for name in self.get_names()]
        if n == None:
            n = [None] * self.get_output_dims()
        elif not isinstance(n, (list, dict)):
            n = [n] * self.get_output_dims()
        elif isinstance(n, dict):
            n = [n[name] for name in self.get_names()]
        if step == None:
            step = [None] * self.get_output_dims()
        elif not isinstance(step, (list, dict)):
            step = [step] * self.get_output_dims()
        elif isinstance(step, dict):
            step = [step[name] for name in self.get_names()]

        if len(start) != len(self.channels) or len(end) != len(self.channels) or len(n) != len(self.channels) or len(step) != len(self.channels):
            raise ValueError("start, end, n, and/or step must be lists of shape (output_dims,n)")

        for i, channel in enumerate(self.channels):
            channel.set_pred_range(start[i], end[i], n[i], step[i])
    
    def get_nyquist_estimation(self):
        """
        Estimate nyquist frequency by taking 0.5/(minimum distance of points).

        Returns:
            list: Nyquist frequency array of shape (input_dims) per channel.

        Examples:
            >>> freqs = dataset.get_nyquist_estimation()
        """
        return [channel.get_nyquist_estimation() for channel in self.channels]
    
    def get_bnse_estimation(self, Q, n=5000):
        """
        Peaks estimation using BNSE (Bayesian Non-parametric Spectral Estimation).

        Args:
            Q (int): Number of peaks to find, defaults to 1.
            n (int): Number of points of the grid to evaluate frequencies, defaults to 5000.

        Returns:
            list: Amplitude array of shape (input_dims,Q) per channel.
            list: Frequency array of shape (input_dims,Q) per channel.
            list: Variance array of shape (input_dims,Q) per channel.

        Examples:
            >>> amplitudes, means, variances = dataset.get_bnse_estimation()
        """
        amplitudes = []
        means = []
        variances = []
        for channel in self.channels:
            channel_amplitudes, channel_means, channel_variances = channel.get_bnse_estimation(Q, n)
            amplitudes.append(channel_amplitudes)
            means.append(channel_means)
            variances.append(channel_variances)
        return amplitudes, means, variances
    
    def get_ls_estimation(self, Q, n=50000):
        """
        Peaks estimation using Lomb Scargle.

        Args:
            Q (int): Number of peaks to find, defaults to 1.
            n (int): Number of points of the grid to evaluate frequencies, defaults to 50000.

        Returns:
            list: Amplitude array of shape (input_dims,Q) per channel.
            list: Frequency array of shape (input_dims,Q) per channel.
            list: Variance array of shape (input_dims,Q) per channel.

        Examples:
            >>> amplitudes, means, variances = dataset.get_ls_estimation()
        """
        amplitudes = []
        means = []
        variances = []
        for channel in self.channels:
            channel_amplitudes, channel_means, channel_variances = channel.get_ls_estimation(Q, n)
            amplitudes.append(channel_amplitudes)
            means.append(channel_means)
            variances.append(channel_variances)
        return amplitudes, means, variances

    def to_kernel(self):
        """
        Return the data vectors in the format as used by the kernels.

        Returns:
            numpy.ndarray: X data of shape (n,2) where X[:,0] contains the channel indices and X[:,1] the X values.
            numpy.ndarray: Y data.

        Examples:
            >>> x, y = dataset.to_kernel()
        """
        x = [channel.X[channel.mask] for channel in self.channels]
        y = [channel.Y[channel.mask] for channel in self.channels]

        chan = [i * np.ones(len(x[i])) for i in range(len(x))]
        chan = np.concatenate(chan).reshape(-1, 1)
        
        x = np.concatenate(x)
        x = np.concatenate((chan, x), axis=1)
        if y == None:
            return x

        y = np.concatenate(y).reshape(-1, 1)
        return x, y

    def to_kernel_pred(self):
        """
        Return the prediction input vectors in the format as used by the kernels.

        Returns:
            numpy.ndarray: X data of shape (n,2) where X[:,0] contains the channel indices and X[:,1] the X values.

        Examples:
            >>> x = dataset.to_kernel_pred()
        """
        x = [channel.X_pred for channel in self.channels]

        chan = [i * np.ones(len(x[i])) for i in range(len(x))]
        chan = np.concatenate(chan).reshape(-1, 1)
        if len(chan) == 0:
            return np.array([]).reshape(-1, 1)

        x = np.concatenate(x)
        x = np.concatenate((chan, x), axis=1)
        return x

    def from_kernel_pred(self, name, mu, var):
        """
        Returns the predictions from the format as used by the kernels. The prediction is stored in the Data class by the given name.

        Args:
            name (str): Name to store the prediction under.
            mu (numpy.ndarray): Y mean prediction of shape (m*n(m)), i.e. a flat array of n(m) data points per channel m.
            var (numpy.ndarray): Y variance prediction of shape (m*n(m)), i.e. a flat array of n(m) data points per channel m.

        Examples:
            >>> x = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
            >>> mu, var = model.model.predict_f(x)
            >>> dataset.from_kernel_pred('MOSM', mu, var)
        """
        N = [len(channel.X_pred) for channel in self.channels]
        if len(mu) != len(var) or sum(N) != len(mu):
            raise ValueError("prediction mu or var different length from prediction x")

        i = 0
        for idx in range(len(self.channels)):
            self.channels[idx].Y_mu_pred[name] = np.squeeze(mu[i:i+N[idx]])
            self.channels[idx].Y_var_pred[name] = np.squeeze(var[i:i+N[idx]])
            i += N[idx]

    def copy(self):
        """
        Make a deep copy of DataSet.

        Returns:
            mogptk.dataset.DataSet

        Examples:
            >>> other = dataset.copy()
        """
        return copy.deepcopy(self)

    def plot(self, title=None, figsize=(12, 8)):
        """
        Plot each Data channel.

        Args:
            title (str, optional): Set the title of the plot.

        Returns:
            matplotlib.figure.Figure: The figure.
            list of matplotlib.axes.Axes: List of axes.

        Examples:
            >>> fig, axes = dataset.plot('Title')
        """
        fig, axes = plt.subplots(self.get_output_dims(), 1, constrained_layout=True, squeeze=False, figsize=figsize)
        if title != None:
            fig.suptitle(title)

        for channel in range(self.get_output_dims()):
            self.channels[channel].plot(ax=axes[channel,0])

        return fig, axes
