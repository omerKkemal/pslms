# =========================================================================== #
# Author: Omer Kemal                                                          #
# =========================================================================== #

from flask import Blueprint

parent = Blueprint(
    'parent', __name__,
    static_folder='static',
    static_url_path='/static',
    template_folder='templates'
)