import numpy as np
import time
import tensorflow_encrypted as tfe

class FakeInputProvider(tfe.NumpyInputProvider):

    def __init__(self, device_name):
        super(FakeInputProvider, self).__init__(device_name)

    @property
    def num_rows(self):
        return 1000

    @property
    def num_cols(self):
        return (2,1)

    def _build_data_generator(self):

        def generate_fake_training_data():
            np.random.seed(42)

            data_size = self.num_rows

            # generate features
            X0 = np.random.multivariate_normal([0, 0], [[1, .75],[.75, 1]], data_size//2)
            X1 = np.random.multivariate_normal([1, 4], [[1, .75],[.75, 1]], data_size//2)
            X = np.vstack((X0, X1)).astype(np.float32)

            # generate labels
            Y0 = np.zeros(data_size//2).reshape(-1, 1)
            Y1 = np.ones (data_size//2).reshape(-1, 1)
            Y = np.vstack((Y0, Y1)).astype(np.float32)

            # shuffle
            perm = np.random.permutation(len(X))
            X = X[perm]
            Y = Y[perm]
            
            return X, Y

        return generate_fake_training_data

input_providers = [
    FakeInputProvider('/job:localhost/replica:0/task:0/device:CPU:3'),
    FakeInputProvider('/job:localhost/replica:0/task:0/device:CPU:4'),
    FakeInputProvider('/job:localhost/replica:0/task:0/device:CPU:5')
]

server0 = tfe.protocol.Server('/job:localhost/replica:0/task:0/device:CPU:0')
server1 = tfe.protocol.Server('/job:localhost/replica:0/task:0/device:CPU:1')
crypto_producer = tfe.protocol.CryptoProducer('/job:localhost/replica:0/task:0/device:CPU:2')

with tfe.local_session(num_players=6) as sess:

    with tfe.protocol.Pond(server0, server1, crypto_producer):

        begin = time.time()

        print("Creating a classifier...")
        logreg = tfe.estimator.LogisticClassifier(
            session=sess,
            num_features=2
        )

        print("Preparing training data...")
        logreg.prepare_training_data(input_providers)
        
        print("Training...")
        logreg.train(epochs=100, batch_size=30)

        print(time.time() - begin)

        # print(logreg.predict(np.array([1., .5])))
