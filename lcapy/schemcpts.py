"""
This module defines and draws the schematic components using
circuitikz.   The components are defined at the bottom of this file.

Copyright 2015, 2016 Michael Hayes, UCECE
"""


from __future__ import print_function
from lcapy.latex import latex_str, format_label
from lcapy.schemmisc import Pos
import numpy as np
import sys

module = sys.modules[__name__]


class Cpt(object):

    voltage_keys = ('v', 'v_', 'v^', 'v_>', 'v_<', 'v^>', 'v^<')
    current_keys = ('i', 'i_', 'i^', 'i_>',  'i_<', 'i^>', 'i^<',
                    'i>_', 'i<_', 'i>^', 'i<^')
    label_keys = ('l', 'l_', 'l^')
    # The following keys do not get passed through to circuitikz.
    misc_keys = ('left', 'right', 'up', 'down', 'rotate', 'size',
                 'dir', 'mirror', 'scale')

    def anon(self, cpt_type):

        sch = self.sch
        if cpt_type not in sch.anon:
            sch.anon[cpt_type] = 0
        sch.anon[cpt_type] += 1        
        return str(sch.anon[cpt_type])

    def __init__(self, sch, cpt_type, cpt_id, string, opts_string, nodes, *args):

        self.sch = sch
        self.type = cpt_type
        self.id = cpt_id

        if cpt_id == '' and sch is not None:
            cpt_id = '@' + self.anon(cpt_type)

        name = self.type + cpt_id

        self.net = string.split(';')[0]
        self.opts_string = opts_string
        # There are three sets of nodes:
        # 1. nodes are the names of the electrical nodes for a cpt.
        # 2. vnodes are the subset of the electrical nodes for a cpt that are drawn.
        # 3. dnodes includes vnodes plus inherited nodes from other cpts (K).  The
        # lookup of this attribute is deferred until cpts are drawn.
        self.nodes = nodes
        self.name = name
        self.args = args
        self.classname = self.__class__.__name__
        self.opts = {}

    def __repr__(self):
        return self.__str__()

    def __str__(self):

        if self.opts == {}:
            return self.net
        return self.net + '; ' + str(self.opts)

    @property
    def size(self):
        """Component size between its nodes"""
        return float(self.opts.get('size', 1.0))

    @property
    def scale(self):
        """This is only used for scaling an opamp"""
        return float(self.opts.get('scale', 1.0))

    @property
    def down(self):
        return self.opts['dir']  == 'down'

    @property
    def up(self):
        return self.opts['dir']  == 'up'

    @property
    def left(self):
        return self.opts['dir']  == 'left'

    @property
    def right(self):
        return self.opts['dir']  == 'right'

    @property
    def horizontal(self):
        return self.opts['dir'] in ('left', 'right')

    @property
    def vertical(self):
        return self.opts['dir'] in ('left', 'down')

    @property
    def mirror(self):
        return 'mirror' in self.opts

    @property
    def angle(self):
        """Return rotation angle"""
        if self.right:
            angle = 0   
        elif self.down:
            angle = -90
        elif self.left:
            angle = 180
        elif self.up:
            angle = 90
        else:
            raise ValueError('Unknown orientation: %s' % self.opts['dir'])
        
        if 'rotate' in self.opts:
            angle += float(self.opts['rotate'])
        return angle

    @property
    def R(self):
        """Return rotation matrix"""
        angle = self.angle
        
        Rdict = {0: ((1, 0), (0, 1)),
                 90: ((0, 1), (-1, 0)),
                 180: ((-1, 0), (0, -1)),
                 -180: ((-1, 0), (0, -1)),
                 -90: ((0, -1), (1, 0))}
        if angle in Rdict:
            return np.array(Rdict[angle])
        
        t = angle / 180.0 * np.pi
        return np.array(((np.cos(t), np.sin(t)),
                         (-np.sin(t), np.cos(t))))

    @property
    def variable(self):
        return 'variable' in self.opts

    @property
    def vnodes(self):
        '''Visible nodes'''
        return self.nodes

    @property
    def dnodes(self):
        '''Nodes used to construct schematic'''
        return self.vnodes

    @property
    def coords(self):
        """Return coordinates of each of the nodes"""
        raise NotImplementedError('coords method not implemented for %s' % self)

    @property
    def tcoords(self):
        """Transformed coordinates for each of the nodes"""
        if hasattr(self, '_tcoords'):
            return self._tcoords

        self._tcoords = np.dot(np.array(self.coords), self.R)
        return self._tcoords

    @property
    def xvals(self):
        return self.tcoords[:, 0]

    @property
    def yvals(self):
        return self.tcoords[:, 1]

    def xlink(self, graphs):

        xvals = self.xvals
        for m1, n1 in enumerate(self.dnodes):
            for m2, n2 in enumerate(self.dnodes[m1 + 1:], m1 + 1):
                if xvals[m2] == xvals[m1]:
                    graphs.link(n1, n2)

    def ylink(self, graphs):

        yvals = self.yvals
        for m1, n1 in enumerate(self.dnodes):
            for m2, n2 in enumerate(self.dnodes[m1 + 1:], m1 + 1):
                if yvals[m2] == yvals[m1]:
                    graphs.link(n1, n2)

    def xplace(self, graphs):

        size = self.size
        xvals = self.xvals
        for m1, n1 in enumerate(self.dnodes):
            for m2, n2 in enumerate(self.dnodes[m1 + 1:], m1 + 1):
                value = (xvals[m2] - xvals[m1]) * size
                graphs.add(n1, n2, value)

    def yplace(self, graphs):

        size = self.size
        yvals = self.yvals
        for m1, n1 in enumerate(self.dnodes):
            for m2, n2 in enumerate(self.dnodes[m1 + 1:], m1 + 1):
                value = (yvals[m2] - yvals[m1]) * size
                graphs.add(n1, n2, value)

    def _node_str(self, node1, node2, **kwargs):

        draw_nodes = kwargs.get('draw_nodes', True)

        node_str = ''
        if node1.visible(draw_nodes):
            node_str = 'o' if node1.port else '*'

        node_str += '-'

        if node2.visible(draw_nodes):
            node_str += 'o' if node2.port else '*'

        if node_str == '-':
            node_str = ''
        
        return node_str

    def _draw_node(self, n, **kwargs):

        draw_nodes = kwargs.get('draw_nodes', True)        

        s = ''
        if not draw_nodes:
            return s

        node = self.sch.nodes[n]
        if not node.visible(draw_nodes):
            return s

        if node.port:
            s = r'  \draw (%s) node[ocirc] {};''\n' % node.name
        else:
            s = r'  \draw (%s) node[circ] {};''\n' % node.name

        return s

    def _draw_nodes(self, **kwargs):

        s = ''
        for n in self.dnodes:
            s += self._draw_node(n, **kwargs)
        return s

    def draw(self, **kwargs):
        raise NotImplementedError('draw method not implemented for %s' % self)

    def opts_str(self, choices):

        def fmt(key, val):
            return '%s=%s' % (key, format_label(val))

        return ','.join([fmt(key, val) 
                         for key, val in self.opts.items()
                         if key in choices])

    @property
    def voltage_str(self):

        return self.opts_str(self.voltage_keys)

    @property
    def current_str(self):

        return self.opts_str(self.current_keys)

    @property
    def label_str(self):

        return self.opts_str(self.label_keys)

    @property
    def args_str(self):

        def fmt(key, val):
            return '%s=%s' % (key, format_label(val))

        return ','.join([fmt(key, val) 
                         for key, val in self.opts.items()
                         if key not in self.voltage_keys + self.current_keys + self.label_keys + self.misc_keys])


    def label(self, **kwargs):

        label_values = kwargs.get('label_values', True)
        label_str = self.default_label if label_values else ''

        # Override label if specified.  There are no placement options.
        str =  ','.join([format_label(val)
                         for key, val in self.opts.items()
                         if key in ('l', )])

        if str != '':
            label_str = str
        return label_str


class Transistor(Cpt):
    """Transistor"""
    
    npos = ((1, 1.5), (0, 0.75), (1, 0))
    ppos = ((1, 0), (0, 0.75), (1, 1.5))

    @property
    def coords(self):
        if self.classname in ('Qpnp', 'Mpmos', 'Jpjf'):
            return self.npos if self.mirror else self.ppos
        else:
            return self.ppos if self.mirror else self.npos

    def draw(self, **kwargs):

        p1, p2, p3 = [self.sch.nodes[n].pos for n in self.dnodes]
        centre = (p1 + p3) * 0.5

        s = r'  \draw (%s) node[%s, %s, scale=2, rotate=%d] (%s) {};''\n' % (
            centre, self.tikz_cpt, self.args_str, self.angle, self.name)
        s += r'  \draw (%s) node[] {%s};''\n'% (centre, self.label(**kwargs))

        # Add additional wires.
        if self.tikz_cpt in ('pnp', 'npn'):
            s += r'  \draw (%s.C) -- (%s) (%s.B) -- (%s) (%s.E) -- (%s);''\n' %(self.name, self.dnodes[0], self.name, self.dnodes[1], self.name, self.dnodes[2])
        else:
            s += r'  \draw (%s.D) -- (%s) (%s.G) -- (%s) (%s.S) -- (%s);''\n' % (self.name, self.dnodes[0], self.name, self.dnodes[1], self.name, self.dnodes[2])

        s += self._draw_nodes(**kwargs)
        return s


class JFET(Transistor):
    """Transistor"""
    
    npos = ((1, 1.5), (0, 0.48), (1, 0))
    ppos = ((1, 0), (0, 1.02), (1, 1.5))


class MOSFET(Transistor):
    """Transistor"""
    
    npos = ((0.85, 1.52), (-0.25, 0.76), (0.85, 0))
    ppos = ((0.85, 0), (-0.25, 0.76), (0.85, 1.52))


class TwoPort(Cpt):
    """Two-port"""

    @property
    def coords(self):
        return ((1, 1), (1, 0), (0, 1), (0, 0))

    def draw(self, **kwargs):

        # TODO, fix positions if component rotated.

        p1, p2, p3, p4 = [self.sch.nodes[n].pos for n in self.dnodes]
        width = p2.x - p4.x
        extra = 0.25
        p1.y += extra
        p2.y -= extra
        p3.y += extra
        p4.y -= extra
        centre = (p1 + p2 + p3 + p4) * 0.25
        top = Pos(centre.x, p1.y + 0.15)

        titlestr = "%s-parameter two-port" % self.args[2]

        s = r'  \draw (%s) -- (%s) -- (%s) -- (%s) -- (%s);''\n' % (
            p4, p3, p1, p2, p4)
        s += r'  \draw (%s) node[minimum width=%.1f] (%s) {%s};''\n' % (
            centre, width, titlestr, self.name)
        s += r'  \draw (%s) node[minimum width=%.1f] {%s};''\n' % (
            top, width, self.label(**kwargs))

        s += self._draw_nodes(**kwargs)
        return s


class TF1(TwoPort):
    """Transformer"""

    def draw(self, **kwargs):

        link = kwargs.get('link', True)

        p1, p2, p3, p4 = [self.sch.nodes[n].pos for n in self.dnodes]

        xoffset = 0.1
        yoffset = 0.5 * self.sch.cpt_size

        # TODO, fix positions if component rotated.
        primary_dot = Pos(p3.x - xoffset, 0.5 * (p3.y + p4.y) + yoffset)
        secondary_dot = Pos(p1.x + xoffset, 0.5 * (p1.y + p2.y) + yoffset)

        centre = (p1 + p2 + p3 + p4) * 0.25
        labelpos = Pos(centre.x, primary_dot.y)

        s = r'  \draw (%s) node[circ] {};''\n' % primary_dot
        s += r'  \draw (%s) node[circ] {};''\n' % secondary_dot
        s += r'  \draw (%s) node[minimum width=%.1f] (%s) {%s};''\n' % (
            labelpos, 0.5, self.label(**kwargs), self.name)

        if link:
            width = p1.x - p3.x
            arcpos = Pos((p1.x + p3.x) / 2, secondary_dot.y - width / 2 + 0.2)

            s += r'  \draw [<->] ([shift=(45:%.2f)]%s) arc(45:135:%.2f);''\n' % (
                width / 2, arcpos, width / 2)

        return s


class TF(TF1):
    """Transformer"""

    def draw(self, **kwargs):

        n1, n2, n3, n4 = self.dnodes

        s = r'  \draw (%s) to [inductor] (%s);''\n' % (n3, n4)
        s += r'  \draw (%s) to [inductor] (%s);''\n' % (n1, n2)

        s += super(TF, self).draw(link=True, **kwargs)
        s += self._draw_nodes(**kwargs)
        return s


class K(TF1):
    """Mutual coupling"""

    def __init__(self, sch, cpt_type, cpt_id, string, opts_string, nodes, *args):

        self.Lname1 = args[0]
        self.Lname2 = args[1]
        super (K, self).__init__(sch, cpt_type, cpt_id, string, opts_string, nodes, *args[2:])

    @property
    def dnodes(self):

        # L1 and L2 need to be previously defined so we can find their nodes.
        L1 = self.sch.elements[self.Lname1]
        L2 = self.sch.elements[self.Lname2]
        return L1.nodes + L2.nodes


class OnePort(Cpt):
    """OnePort"""

    @property
    def coords(self):
        return ((0, 0), (1, 0))

    def draw(self, **kwargs):

        label_values = kwargs.get('label_values', True)
        label_ids = kwargs.get('label_ids', True)

        n1, n2 = self.dnodes

        tikz_cpt = self.tikz_cpt
        if self.type == 'R' and self.variable:
            tikz_cpt = 'vR'

        label_pos = '_'
        voltage_pos = '^'
        if self.type in ('V', 'I', 'E', 'F', 'G', 'H'):

            # circuitikz expects the positive node first, except for
            # voltage and current sources!  So swap the nodes
            # otherwise they are drawn the wrong way around.
            n1, n2 = n2, n1

            if self.horizontal:
                # Draw label on LHS for vertical cpt and below
                # for horizontal cpt.
                label_pos = '^'
                voltage_pos = '_'
        else:
            if self.vertical:
                # Draw label on LHS for vertical cpt and below
                # for horizontal cpt.
                label_pos = '^'
                voltage_pos = '_'

        # Add modifier to place voltage label on other side
        # from component identifier label.
        if 'v' in self.opts:
            self.opts['v' + voltage_pos] = self.opts.pop('v')

        # Reversed voltage.
        if 'vr' in self.opts:
            self.opts['v' + voltage_pos + '>'] = self.opts.pop('vr')

        current_pos = label_pos
        # Add modifier to place current label on other side
        # from voltage marks.
        if 'i' in self.opts:
            self.opts['i' + current_pos] = self.opts.pop('i')

        # Reversed current.
        if 'ir' in self.opts:
            self.opts['i' + current_pos + '<'] = self.opts.pop('ir')

        if 'l' in self.opts:
            self.opts['l' + label_pos] = self.opts.pop('l')

        node_str = self._node_str(self.sch.nodes[n1], self.sch.nodes[n2],
                                  **kwargs)

        args_str = ','.join([self.args_str, self.voltage_str,
                             self.current_str])

        # Generate default label.
        if (label_ids and label_values and self.id_label != '' 
            and self.value_label):
            label_str = r'l%s={%s=%s}' % (label_pos, self.id_label,
                                          self.value_label)
        elif label_ids and self.id_label != '':
            label_str = 'l%s=%s' % (label_pos, self.id_label)
        elif label_values and self.value_label != '':
            label_str = r'l%s=%s' % (label_pos, self.value_label)
        else:
            label_str = ''

        # Override label if specified.
        if self.label_str != '':
            label_str = self.label_str

        s = r'  \draw (%s) to [align=right,%s,%s,%s,%s,n=%s] (%s);''\n' % (
            n1, tikz_cpt, label_str, args_str, node_str, self.name, n2)
        return s


class VCS(OnePort):
    """Voltage controlled source"""

    @property
    def vnodes(self):
        return self.nodes[0:2]


class CCS(OnePort):
    """Current controlled source"""


class Opamp(Cpt):

    # The Nm node is not used (ground).
    ppos = ((2.4, 0.0), (0, 0.5), (0, -0.5))
    npos = ((2.4, 0.0), (0, -0.5), (0, 0.5))

    @property
    def vnodes(self):
        return (self.nodes[0], ) + self.nodes[2:]

    @property
    def coords(self):
        return self.npos if self.mirror else self.ppos

    def draw(self, **kwargs):

        p1, p3, p4 = [self.sch.nodes[n].pos for n in self.dnodes]
        n1, n3, n4 = self.dnodes

        centre = (p3 + p4) * 0.25 + p1 * 0.5

        yscale = 2 * 1.019 * self.scale
        if not self.mirror:
            yscale = -yscale

        # Note, scale scales by area, xscale and yscale scale by length.
        s = r'  \draw (%s) node[op amp, %s, xscale=%.3f, yscale=%.3f, rotate=%d] (%s) {};''\n' % (
            centre, self.args_str, 2 * 1.01 * self.scale, yscale,
            self.angle, self.name)
        s += r'  \draw (%s.out) |- (%s);''\n' % (self.name, n1)
        s += r'  \draw (%s.+) |- (%s);''\n' % (self.name, n3)
        s += r'  \draw (%s.-) |- (%s);''\n' % (self.name, n4)
        # Draw label separately to avoid being scaled by 2.
        s += r'  \draw (%s) node[] {%s};''\n' % (centre, self.label(**kwargs))
        
        s += self._draw_nodes(**kwargs)
        return s


class FDOpamp(Cpt):

    npos = ((2.05, 1), (2.05, 0), (0, 0), (0, 1))
    ppos = ((2.05, -1), (2.05, 0), (0, 0), (0, -1))


    @property
    def coords(self):
        return self.npos if self.mirror else self.ppos

    def draw(self, **kwargs):

        p1, p2, p3, p4 = [self.sch.nodes[n].pos for n in self.dnodes]
        n1, n2, n3, n4 = self.dnodes

        centre = (p1 + p2 + p3 + p4) * 0.25 + np.dot((0.15, 0), self.R) * self.scale

        yscale = 2 * 1.02 * self.scale
        if not self.mirror:
            yscale = -yscale

        s = r'  \draw (%s) node[fd op amp, %s, xscale=%.3f, yscale=%.3f, rotate=%d] (%s) {};''\n' % (
            centre, self.args_str, 2 * 1.01 * self.scale, yscale,
            self.angle, self.name)
        s += r'  \draw (%s.out +) |- (%s);''\n' % (self.name, n1)
        s += r'  \draw (%s.out -) |- (%s);''\n' % (self.name, n2)
        s += r'  \draw (%s.+) |- (%s);''\n' % (self.name, n3)
        s += r'  \draw (%s.-) |- (%s);''\n' % (self.name, n4)
        # Draw label separately to avoid being scaled by 2.
        s += r'  \draw (%s) node[] {%s};''\n' % (centre, self.label(**kwargs))
        
        s += self._draw_nodes(**kwargs)
        return s


class SPDT(Cpt):
    """SPDT switch"""

    @property
    def coords(self):
        return ((0, 0.15), (0.6, 0.3), (0.6, 0))

    def draw(self, **kwargs):

        p1, p2, p3 = [self.sch.nodes[n].pos for n in self.dnodes]

        centre = p1 * 0.5 + (p2 + p3) * 0.25
        s = r'  \draw (%s) node[spdt, %s, rotate=%d] (%s) {};''\n' % (
            centre, self.args_str, self.angle, self.name)
        
        # TODO, fix label position.
        centre = (p1 + p3) * 0.5 + Pos(0, -0.5)
        s += r'  \draw (%s) node[] {%s};''\n' % (centre, self.label(**kwargs))
        s += self._draw_nodes(**kwargs)
        return s


class Logic(Cpt):
    """Logic"""

    @property
    def coords(self):
        return ((0, 0), (0.75, 0))

    def draw(self, **kwargs):

        # TODO, fix scaling to make buffer and inverter same size.

        p1, p2 = [self.sch.nodes[n].pos for n in self.dnodes]
        centre = (p1 + p2) * 0.5
        s = r'  \draw (%s) node[align=left, %s, %s, rotate=%d] (%s) {};''\n' % (
            centre, self.tikz_cpt, self.args_str, self.angle, self.name)
        s += r'  \draw (%s) node[] {%s};''\n' % (centre, self.label(**kwargs))
        s += self._draw_nodes(**kwargs)
        return s


class Wire(OnePort):

    @property
    def coords(self):

        if 'implicit' in self.opts or 'ground' in self.opts or 'sground' in self.opts:
            return ((0, 0), )
        return ((0, 0), (1, 0))

    @property
    def vnodes(self):

        if 'implicit' in self.opts or 'ground' in self.opts or 'sground' in self.opts:
            return (self.nodes[0], )
        return self.nodes

    def draw_implicit(self, **kwargs):
        """Draw implict wires, i.e., connections to ground, etc."""

        kind = ''
        if 'implicit' in self.opts:
            kind = 'sground'
        elif 'ground' in self.opts:
            kind = 'ground'
        elif 'sground' in self.opts:
            kind = 'sground'

        anchor = 'south west'
        if self.down:
            anchor = 'north west'

        n1 = self.dnodes[0]
        s = r'  \draw (%s) node[%s,scale=0.5,rotate=%d] {};''\n' % (
            n1, kind, self.angle + 90)

        lpos = self.sch.nodes[n1].pos + np.dot((0.25, 0), self.R)

        if 'l' in self.opts:
            s += r'  \draw [anchor=%s] (%s) node {%s};''\n' % (
                anchor, lpos, self.label(**kwargs))
        return s

    def draw(self, **kwargs):

        if 'implicit' in self.opts or 'ground' in self.opts or 'sground' in self.opts:
            return self.draw_implicit(**kwargs)
                                    
        return super(Wire, self).draw(**kwargs)


classes = {}

def defcpt(name, base, docstring, cpt=None):
    
    if isinstance(base, str):
        base = classes[base]

    newclass = type(name, (base, ), {'__doc__': docstring})

    if cpt is not None:
        newclass.tikz_cpt = cpt
    classes[name] = newclass


def make(classname, parent, cpt_type, cpt_id,
         string, opts_string, nodes, *args):

    # Create instance of component object
    try:
        newclass = getattr(module, classname)
    except:
        newclass = classes[classname]

    cpt = newclass(parent, cpt_type, cpt_id, string, opts_string, 
                   nodes, *args)
    # Add named attributes for the args?   Lname1, etc.
        
    return cpt

# Dynamically create classes.

defcpt('C', OnePort, 'Capacitor', 'C')

defcpt('D', OnePort, 'Diode', 'D')
defcpt('Dled', 'D', 'LED', 'leD')
defcpt('Dphoto', 'D', 'Photo diode', 'pD')
defcpt('Dschottky', 'D', 'Schottky diode', 'zD')
defcpt('Dtunnel', 'D', 'Tunnel diode', 'tD')
defcpt('Dzener', 'D', 'Zener diode', 'zD')

defcpt('E', VCS, 'VCVS', 'american controlled voltage source')
defcpt('Eopamp', Opamp, 'Opamp')
defcpt('Efdopamp', FDOpamp, 'Fully differential opamp')
defcpt('F', VCS, 'CCCS', 'american controlled current source')
defcpt('G', CCS, 'VCCS', 'american controlled current source')
defcpt('H', CCS, 'CCVS', 'american controlled voltage source')

defcpt('I', OnePort, 'Current source', 'I')
defcpt('sI', OnePort, 'Current source', 'I')
defcpt('Isin', 'I', 'Sinusoidal current source', 'sI')
defcpt('Idc', 'I', 'DC current source', 'I')
defcpt('Iac', 'I', 'AC current source', 'sI')

defcpt('J', JFET, 'N JFET transistor', 'njfet')
defcpt('Jnjf', 'J', 'N JFET transistor', 'njfet')
defcpt('Jpjf', 'J', 'P JFET transistor', 'pjfet')

defcpt('L', OnePort, 'Inductor', 'L')

defcpt('M', MOSFET, 'N MOSJFET transistor', 'nmos')
defcpt('Mnmos', 'M', 'N channel MOSJFET transistor', 'nmos')
defcpt('Mpmos', 'M', 'P channel MOSJFET transistor', 'pmos')

defcpt('O', OnePort, 'Open circuit', 'open')
defcpt('P', OnePort, 'Port', 'open')

defcpt('Q', Transistor, 'NPN transistor', 'npn')
defcpt('Qpnp', 'Q', 'PNP transistor', 'pnp')
defcpt('Qnpn', 'Q', 'NPN transistor', 'npn')

defcpt('R', OnePort, 'Resistor', 'R')

defcpt('SW', OnePort, 'Switch', 'closing switch')
defcpt('SWno', 'SW', 'Normally open switch', 'closing switch')
defcpt('SWnc', 'SW', 'Normally closed switch', 'opening switch')
defcpt('SWpush', 'SW', 'Pushbutton switch', 'push button')
defcpt('SWspdt', SPDT, 'SPDT switch', 'spdt')

defcpt('TF', TwoPort, 'Transformer', 'transformer')
defcpt('TP', TwoPort, 'Two port', '')

defcpt('Ubuffer', Logic, 'Buffer', 'buffer')
defcpt('Uinverter', Logic, 'Inverter', 'american not port')

defcpt('V', OnePort, 'Voltage source', 'V')
defcpt('sV', OnePort, 'Voltage source', 'V')
defcpt('Vsin', 'V', 'Sinusoidal voltage source', 'sV')
defcpt('Vdc', 'V', 'DC voltage source', 'V')
defcpt('Vstep', 'V', 'Step voltage source', 'V')
defcpt('Vac', 'V', 'AC voltage source', 'sV')

defcpt('W', Wire, 'Wire', 'short')
defcpt('Y', OnePort, 'Admittance', 'european resistor')
defcpt('Z', OnePort, 'Impedance', 'european resistor')

# Perhaps AM for ammeter, VM for voltmeter, VR for variable resistor?
# Currently, a variable resistor is supported with the variable
# option.
