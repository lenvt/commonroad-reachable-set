import numpy as np
import pytest
from commonroad_reachset.utility import configugation as util_configuration


@pytest.mark.parametrize(
    "length, width, wheelbase, radius_expected",
    [(6, 2, None, 1.5), (0, 2, 4, 1.5), (4.927, 2.208, None, 1.4)],
)
def test_compute_disk_radius_and_wheelbase(length, width, wheelbase, radius_expected):
    _radius, _wheelbase = util_configuration.compute_disc_radius_and_wheelbase(
        length, width, wheelbase
    )

    assert np.isclose(_radius, radius_expected)
    
    # if the wheelbase is not given, check if it is correctly computed
    if not wheelbase:
        assert np.isclose(_wheelbase, length / 3 * 2)
