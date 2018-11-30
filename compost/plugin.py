import importlib

# Note that we delay import of app to the functions which need it,
# since we may want to load plugins during app creation too, and otherwise
# we'd get circular import problems

COMPOST_PLUGIN_CLASS_REFS = {}
COMPOST_PLUGIN_FUNCTION_REFS = {}

class PluginException(Exception):
    pass

def load_class_raw(classpath):
    modpath = ".".join(classpath.split(".")[:-1])
    classname = classpath.split(".")[-1]
    try:
        mod = importlib.import_module(modpath)
    except ImportError as e:
        return None
    klazz = getattr(mod, classname, None)
    return klazz

def load_class(classpath, cache_class_ref=True):
    global COMPOST_PLUGIN_FUNCTION_REFS
    klazz = COMPOST_PLUGIN_CLASS_REFS.get("PLUGIN_CLASS_REFS", {}).get(classpath)
    if klazz is not None:
        return klazz

    klazz = load_class_raw(classpath)
    if klazz is None:
        raise PluginException("Could not load class {x}".format(x=classpath))

    if cache_class_ref:
        COMPOST_PLUGIN_CLASS_REFS[classpath] = klazz

    return klazz

def load_module(modpath):
    return importlib.import_module(modpath)

def load_function_raw(fnpath):
    modpath = ".".join(fnpath.split(".")[:-1])
    fnname = fnpath.split(".")[-1]
    try:
        mod = importlib.import_module(modpath)
    except ImportError:
        return None
    fn = getattr(mod, fnname, None)
    return fn

def load_function(fnpath, cache_fn_ref=True):
    global COMPOST_PLUGIN_FUNCTION_REFS
    fn = COMPOST_PLUGIN_FUNCTION_REFS.get(fnpath)
    if fn is not None:
        return fn

    fn = load_function_raw(fnpath)
    if fn is None:
        raise PluginException("Could not load function {x}".format(x=fnpath))

    if cache_fn_ref:
        COMPOST_PLUGIN_FUNCTION_REFS[fnpath] = fn

    return fn
