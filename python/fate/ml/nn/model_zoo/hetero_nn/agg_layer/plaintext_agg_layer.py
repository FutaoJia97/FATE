import torch
import torch as t
from typing import Union, List
from torch.nn.modules.module import T
from fate.ml.nn.model_zoo.hetero_nn.agg_layer._base import AggLayer


class AggLayerGuest(AggLayer):

    def __init__(self,
                 out_features: int,
                 host_in_features: Union[int, List[int], None],
                 guest_in_features: Union[int, None],
                 activation: str = "relu",
                 ):
        super(AggLayerGuest, self).__init__()
        self._out_features = out_features
        self._guest_in_features = guest_in_features

        assert activation in ["relu", "sigmoid", "tanh"], "activation should be relu, sigmoid or tanh"

        if guest_in_features is not None:
            assert isinstance(guest_in_features, int), "guest_in_features should be int"
            self._guest_model = t.nn.Linear(guest_in_features, out_features)
        else:
            self._guest_model = None

        assert isinstance(host_in_features, (int, list)), "host_in_features should be int or list[int]"
        self._host_model = t.nn.ModuleList()
        if isinstance(host_in_features, int):
            host_in_features = [host_in_features]
        for host_in_feature in host_in_features:
            self._host_model.append(t.nn.Linear(host_in_feature, out_features))

        if activation == "relu":
            self._activation_layer = t.nn.ReLU()
        elif activation == "sigmoid":
            self._activation_layer = t.nn.Sigmoid()
        elif activation == "tanh":
            self._activation_layer = t.nn.Tanh()

        self._host_num = len(self._host_model)
        self._guest_input_cache = None
        self._host_input_caches = None
        self._out_cache = None

        self.training = True

    def train(self: T, mode: bool = True) -> T:
        self.training = mode
        return self

    def eval(self: T) -> T:
        self.training = False
        return self

    def _clear_state(self):
        self._guest_input_cache = None
        self._host_input_caches = None
        self._out_cache = None

    def _forward(self, x_g: t.Tensor = None, x_h: List[t.Tensor] = None) -> t.Tensor:

        if x_g is None and x_h is None:
            raise ValueError("guest input and host inputs cannot be both None")

        if x_g is not None:
            guest_out = self._guest_model(x_g)
        else:
            guest_out = 0

        if x_h is not None:
            for h_idx in range(self._host_num):
                host_out = self._host_model[h_idx](x_h[h_idx])
                guest_out += host_out

        final_out = self._activation_layer(guest_out)
        return final_out

    def forward(self, x: t.Tensor = None) -> t.Tensor:

        if self.training:

            # save input for backwards
            if self._has_ctx:
                self._host_input_caches = []
                host_x = self.ctx.hosts.get(self._fw_suffix.format(self._fw_count))
                self._fw_count += 1
                for h in range(self._host_num):
                    host_input_cache = t.from_numpy(host_x[h]).requires_grad_(True)
                    self._host_input_caches.append(host_input_cache)
            else:
                self._host_input_caches = None

            # if self._guest_model is not None:
            #     self._guest_input_cache = x.detach().requires_grad_(True)
            # else:
            #     self._guest_input_cache = None

            out = self._forward(x, self._host_input_caches)
            final_out = self._activation_layer(out)
            # self._out_cache = final_out
            return final_out

        else:
            return self.predict(x)

    def backward(self, error):

        # compute backward grads
        backward_list = []
        # if self._guest_input_cache is not None:
        #     backward_list.append(self._guest_input_cache)
        #     has_guest_error = 1
        if self._host_input_caches is not None:
            for h in self._host_input_caches:
                backward_list.append(h)
        ret_error = t.autograd.grad(error, backward_list, retain_graph=True)
        # send error back to hosts
        if self._has_ctx:
            host_errors = ret_error
            idx = 0
            for host in self.ctx.hosts:
                host.put(self._bw_suffix.format(self._bw_count), host_errors[idx])
                idx += 1
            self._bw_count += 1

        self._clear_state()

    def predict(self, x):

        # save input for backwards
        host_x = None
        if self._has_ctx:
            host_x = self.ctx.hosts.get(self._pred_suffix.format(self._pred_count))
            self._pred_count += 1
        with torch.no_grad():
            out = self._forward(x, host_x)
            final_out = self._activation_layer(out)
            return final_out.detach()


class AggLayerHost(AggLayer):

    def __init__(self):
        super(AggLayerHost, self).__init__()

    def train(self: T, mode: bool = True) -> T:
        self.training = mode
        return self

    def eval(self: T) -> T:
        self.training = False
        return self

    def forward(self, x: t.Tensor) -> None:
        if self.training:
            assert isinstance(x, t.Tensor), 'x should be a tensor'
            x = x.detach().cpu().numpy()
            self.ctx.guest.put(self._fw_suffix.format(self._fw_count), x)
            self._fw_count += 1
        else:
            self.predict(x)
    def backward(self, error=None) -> t.Tensor:
        error = self.ctx.guest.get(self._bw_suffix.format(self._bw_count))
        self._bw_count += 1
        return error

    def predict(self, x):
        self.ctx.guest.put(self._pred_suffix.format(self._pred_count), x)
        self._pred_count += 1
