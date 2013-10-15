def load(optparser, options):
    if not options.adapter:
        optparser.error("--adapter must be specified")
    mod_name = options.adapter
    mod = __import__(mod_name)
    cls = getattr(mod, mod_name)
    adapter = cls(options)
    return adapter


def add_options(optparser):
    optparser.add_option('', '--debug', action="store_true",
            help='Debug logging')
    optparser.add_option('-a', '--adapter',
            help='Use specified JTAG adapter plugin')
    optparser.add_option('-p', '--port',
            help='Port/device adapter uses')
