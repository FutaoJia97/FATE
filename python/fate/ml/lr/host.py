import logging

import numpy as np
import torch
from fate.arch import tensor
from fate.interface import Context, ModelsLoader, ModelsSaver
from pandas import pandas

from ..abc.module import HeteroModule

logger = logging.getLogger(__name__)


class DataframeMock:
    def __init__(self) -> None:
        self.data = (
            pandas.read_csv(
                "/Users/sage/proj/FATE/2.0.0-alpha/examples/data/breast_hetero_host.csv"
            )
            .to_numpy()
            .astype(np.float32)
        )
        self.num_features = 20
        self.num_sample = len(self.data)

    def batches(self, batch_size):
        num_batchs = (self.num_sample - 1) // batch_size + 1
        for chunk in np.array_split(self.data, num_batchs):
            yield tensor.tensor(torch.Tensor(chunk[:, 1:]))


class LrModuleHost(HeteroModule):
    def __init__(
        self,
        penalty="l2",
        *,
        dual=False,
        tol=1e-4,
        C=1.0,
        fit_intercept=True,
        intercept_scaling=1,
        class_weight=None,
        random_state=None,
        solver="lbfgs",
        max_iter=100,
        multi_class="auto",
        verbose=0,
        warm_start=False,
        n_jobs=None,
        l1_ratio=None,
    ):
        self.max_iter = max_iter
        self.batch_size = 100
        self.alpha = 0.01

    def fit(self, ctx: Context, train_data) -> None:
        # mock data
        train_data = DataframeMock()
        # get encryptor
        encryptor = ctx.arbiter("encryptor").get()

        w = tensor.tensor(
            torch.randn((train_data.num_features, 1), dtype=torch.float32)
        )
        for i, iter_ctx in ctx.range(self.max_iter):
            logger.info(f"start iter {i}")
            j = 0
            for batch_ctx, X in iter_ctx.iter(train_data.batches(self.batch_size)):
                logger.info(f"start batch {j}")
                d_host = 0.25 * tensor.matmul(X, w)
                batch_ctx.guest.put(d_host=encryptor.encrypt(d_host))
                d = batch_ctx.guest.get("d")
                tensor.matmul(X.T, d).to(batch_ctx.arbiter, "g_enc")
                g_plain = batch_ctx.arbiter.get("g")
                w -= (self.alpha / self.batch_size) * g_plain
                logger.info(w)
                j += 1
