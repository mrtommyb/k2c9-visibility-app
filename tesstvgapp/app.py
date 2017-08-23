import matplotlib
matplotlib.use('Agg')

import flask
from flask import Flask, request
from astropy.coordinates import SkyCoord
from mpl_toolkits.basemap import Basemap

try:
    from io import BytesIO  # Python 3
except ImportError:
    from cStringIO import StringIO as BytesIO  # Legacy Python

import tvguide

tvgapp = Flask('tesstvgapp', static_url_path='')


def _parse_single_pos(pos):
    try:
        pos_crd = SkyCoord(pos)
    except ValueError:  # The coordinate string is ambiguous
        if ":" in pos:
            pos_crd = SkyCoord(pos, unit="hour,deg")
        else:
            pos_crd = SkyCoord(pos, unit="deg")
    return pos_crd


def _parse_pos(pos):
    """Parses the 'pos' argument.

    Returns
    -------
    positions : list of `astropy.coordinates.SkyCoord` objects
    """
    if pos is None:
        return []
    positions = [_parse_single_pos(single_pos)
                   for single_pos in pos.split(",")]
    return positions

def _isobservable(ra, dec):
    """is target observable by TESS is cycle 1"""
    tobj = tvguide.TessPointing(ra, dec)
    if tobj.is_observable() == 2:
        return True
    else:
        return False

def _camera(ra, dec):
    "which camera is the target on?"
    tobj = tvguide.TessPointing(ra, dec)
    if _isobservable(ra, dec):
        return tobj.get_camera(fallback=True)
    else:
        return 0

def _getcamera(pos):
    """returns a list of cameras"""
    positions = _parse_pos(pos)
    return [_camera(poscrd.ra.deg, poscrd.dec.deg)
            for poscrd in positions]

def _sectors(ra, dec):
    "which camera is the target on?"
    tobj = tvguide.TessPointing(ra, dec)
    if _isobservable(ra, dec):
        return tobj.get_maxminmedave()[0]
    else:
        return 0

def _getmaxsect(pos):
    """returns a list of cameras"""
    positions = _parse_pos(pos)
    return [_sectors(poscrd.ra.deg, poscrd.dec.deg)
            for poscrd in positions]


def _in_region(pos):
    """Returns a list of booleans."""
    positions = _parse_pos(pos)
    return [_isobservable(poscrd.ra.deg, poscrd.dec.deg)
            for poscrd in positions]

@tvgapp.route('/')
def root():
    return tvgapp.send_static_file('index.html')


@tvgapp.route('/demo')
def demo():
    return flask.redirect("check-visibility?pos=234.56 -78.9,270.5 -28.2")


@tvgapp.route('/in-tess-fov')
def in_tess_fov():
    pos = request.args.get('pos', default=None, type=str)
    fmt = request.args.get('fmt', default=None, type=str)
    input_strings = pos.split(",")
    result = _in_region(pos)
    if fmt == "csv":
        csv = "position,in_region\r\n"
        for idx in range(len(result)):
            csv += input_strings[idx]
            if result[idx]:
                csv += ",yes\r\n"
            else:
                csv += ",no\r\n"
    else:
        csv = ""
        for idx in range(len(result)):
            if result[idx]:
                csv += "yes\r\n"
            else:
                csv += "no\r\n"
    return flask.Response(csv, mimetype='text/plain')


@tvgapp.route('/check-visibility')
def check_visibility():
    pos = request.args.get('pos', default=None, type=str)
    try:
        positions = _parse_pos(pos)
    except Exception:
        return "Error: the input is invalid."
    pos_hmsdms = [poscrd.to_string("hmsdms") for poscrd in positions]
    pos_decimal = [poscrd.to_string("decimal") for poscrd in positions]
    return flask.render_template('check-visibility.html',
                                 pos=pos,
                                 pos_split=pos.split(","),
                                 positions=positions,
                                 pos_hmsdms=pos_hmsdms,
                                 pos_decimal=pos_decimal,
                                 in_region=_in_region(pos),
                                 camera=_getcamera(pos),
                                 maxsect=_getmaxsect(pos))


@tvgapp.route('/tesstvguide.png')
def tesstvguide():
    # The user may optionally mark a position
    pos = request.args.get('pos', default=None, type=str)
    size = request.args.get('size', default=None, type=float)

    positions = _parse_pos(pos)
    # Create the plot
    fovplot = c9.C9FootprintPlot()
    superstamp_patches, channel_patches = fovplot.plot_outline()
    fovplot.fig.tight_layout()
    if len(positions) > 0:
        ra = [poscrd.ra.deg for poscrd in positions]
        dec = [poscrd.dec.deg for poscrd in positions]
        user_position = fovplot.ax.scatter(ra, dec,
                                           marker='+', lw=2.5, s=200,
                                           zorder=900, color="k")
        legend_objects = (user_position, superstamp_patches[0][0])
        legend_labels = ("Your position", "K2C9 Observations")
    else:
        legend_objects = (superstamp_patches[0][0],)
        legend_labels = ("K2C9 Observations",)
    fovplot.ax.legend(legend_objects, legend_labels,
                      bbox_to_anchor=(0.1, 1., 1., 0.), loc=3,
                      ncol=len(legend_objects), borderaxespad=0.,
                      handlelength=0.8, frameon=False,
                      numpoints=1, scatterpoints=1)

    if len(positions) > 0 and size is not None:
        fovplot.ax.set_xlim([max(ra) + size / 2., min(ra) - size / 2.])
        fovplot.ax.set_ylim([min(dec) - size / 2., max(dec) + size / 2.])

    img = BytesIO()
    fovplot.fig.savefig(img)
    img.seek(0)
    response = flask.send_file(img, mimetype="image/png")
    return response
