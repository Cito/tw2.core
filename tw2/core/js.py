"""
Python-JS interface to dynamically create JS function calls from your widgets.

This moudle doesn't aim to serve as a Python-JS "translator". You should code
your client-side code in JavaScript and make it available in static files which
you include as JSLinks or inline using JSSources. This module is only intended
as a "bridge" or interface between Python and JavaScript so JS function
**calls** can be generated programatically.
"""
import sys

import logging
from itertools import imap

import warnings

from tw2.core import JSFuncCall

__all__ = ["js_callback", "js_function", "js_symbol"]

log = logging.getLogger(__name__)

#class TWEncoder(simplejson.encoder.JSONEncoder):
#    """A JSON encoder that can encode Widgets, js_calls, js_symbols and
#    js_callbacks.
#
#    Example::
#
#        >> encode = TWEncoder().encode
#        >> print encode({'onLoad': js_function("do_something")(js_symbol("this"))})
#        {"onLoad": do_something(this)}
#
#        >> from tw2.core.api import Widget
#        >> w = Widget("foo")
#        >> args = {'onLoad': js_callback(js_function('jQuery')(w).click(js_symbol('onClick')))}
#        >> print encode(args)
#        {"onLoad": function(){jQuery(\\"foo\\").click(onClick)}}
#        >> print encode({'args':args})
#        {"args": {"onLoad": function(){jQuery(\\"foo\\").click(onClick)}}}
#
#
#
#    """
#    def __init__(self, *args, **kw):
#        self.pass_through = (_js_call, js_callback, js_symbol, js_function)
#        super(TWEncoder, self).__init__(*args, **kw)

#    def default(self, obj):
#        if isinstance(obj, self.pass_through):
#            return self.mark_for_escape(obj)
#        elif hasattr(obj, '_id'):
#            return str(obj.id)
#        return super(TWEncoder, self).default(obj)

#    def encode(self, obj):
#        encoded = super(TWEncoder, self).encode(obj)
#        return self.unescape_marked(encoded)

#    def mark_for_escape(self, obj):
#        return '*#*%s*#*' % obj

#    def unescape_marked(self, encoded):
#        return encoded.replace('"*#*','').replace('*#*"', '')


def js_symbol(name):
    warnings.warn("js_symbol will soon be deprecated, use JSSymbol instead.",
    DeprecationWarning)
    from resources import JSSymbol
    return JSSymbol(name)


class js_callback(object):
    """A js function that can be passed as a callback to be called
    by another JS function

    Examples:

    .. sourcecode:: python

        >> str(js_callback("update_div"))
        'update_div'

        >> str(js_callback("function (event) { .... }"))
        'function (event) { .... }'

        # Can also create callbacks for deferred js calls

        >> str(js_callback(js_function('foo')(1,2,3)))
        'function(){foo(1, 2, 3)}'

        # Or equivalently

        >> str(js_callback(js_function('foo'), 1,2,3))
        'function(){foo(1, 2, 3)}'

        # A more realistic example

        >> jQuery = js_function('jQuery')
        >> my_cb = js_callback('function() { alert(this.text)}')
        >> on_doc_load = jQuery('#foo').bind('click', my_cb)
        >> call = jQuery(js_callback(on_doc_load))
        >> print call
        jQuery(function(){jQuery(\\"#foo\\").bind(\\"click\\", \
            function() { alert(this.text)})})

    """
    def __init__(self, cb, *args):
        warnings.warn('js_callback is being deprecated in future releases.',
            DeprecationWarning)
        if isinstance(cb, basestring):
            self.cb = cb
        elif isinstance(cb, js_function) or 'JSFuncCall' in repr(cb):
            if args:
                cbs = cb.req(args=args)
            else:
                cbs = cb.req()
            cbs.prepare()
            self.cb = "function(){%s}" % str(cbs)
        elif isinstance(cb, _js_call):
            self.cb = "function(){%s}" % cb
        else:
            self.cb = ''

    def __call__(self, *args):
        raise TypeError("A js_callback cannot be called from Python")

    def __str__(self):
        return self.cb


class js_function(object):
    """A JS function that can be "called" from python and and added to
    a widget by widget.add_call() so it get's called every time the widget
    is rendered.

    Used to create a callable object that can be called from your widgets to
    trigger actions in the browser. It's used primarily to initialize JS code
    programatically. Calls can be chained and parameters are automatically
    json-encoded into something JavaScript undersrtands. Example::

    .. sourcecode:: python

        >> jQuery = js_function('jQuery')
        >> call = jQuery('#foo').datePicker({'option1': 'value1'})
        >> str(call)
        'jQuery("#foo").datePicker({"option1": "value1"})'

    Calls are added to the widget call stack with the ``add_call`` method.

    If made at Widget initialization those calls will be placed in
    the template for every request that renders the widget.

    .. sourcecode:: python

        >> from tw.api import Widget
        >> class SomeWidget(Widget):
        ...     params = ["pickerOptions"]
        ...     pickerOptions = {}
        ...     def __init__(self, *args, **kw):
        ...         super(SomeWidget, self).__init__(*args, **kw)
        ...         self.add_call(
        ...             jQuery('#%s' % self.id).datePicker(self.pickerOptions)
        ...         )

    If we want to dynamically make calls on every request, we ca also add_calls
    inside the ``prepare`` method.

    .. sourcecode:: python

        >> class SomeWidget(Widget):
        ...     params = ["pickerOptions"]
        ...     pickerOptions = {}
        ...     def prepare(self):
        ...         super(SomeWidget, self).prepare()
        ...         self.add_call(
        ...             jQuery('#%s' % d.id).datePicker(d.pickerOptions)
        ...         )

    This would allow to pass different options to the datePicker on every
    display.

    JS calls are rendered by the same mechanisms that render required css and
    js for a widget and places those calls at bodybottom so DOM elements which
    we might target are available.

    Examples:

    .. sourcecode:: python

       >> call = js_function('jQuery')("a .async")
       >> str(call)
       'jQuery("a .async")'

       # js_function calls can be chained:

       >> call = js_function('jQuery')("a .async").foo().bar()
       >> str(call)
       'jQuery("a .async").foo().bar()'

    """
    def __init__(self, name):
        warnings.warn('js_function is being deprecated in future releases.' + \
            'Please update your widgets to use JSFuncCall.',
            DeprecationWarning)
        self.__name = name

    def __call__(self, *args):
        return JSFuncCall(function=self.__name, args=args)
        #return _js_call(self.__name, args)

#class _js_call(object):
#    def __init__(self, name, args=None):
#        self.__name = name
#        self.__args = args
#        self.__src = None

#    def __call__(self, *args):
#        self.__args = args
#        self.__called = True
#        return self

#    def __get_js_repr(self):
#        from resources import encoder
#        if not self.__src:
#            args = self.__args
#            self.__src = '%s(%s)' % (
#                self.__name,
#                ', '.join(imap(encoder.encode, args))
#            )
#            return self.__src
#        else:
#            return self.__name

#    def __str__(self):
#        return self.__get_js_repr()

#    def __unicode__(self):
#        return str(self).decode(sys.getdefaultencoding())

#encode = TWEncoder().encode
