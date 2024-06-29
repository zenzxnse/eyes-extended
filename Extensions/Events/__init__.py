import pkgutil

EVENTS = [module.name for module in pkgutil.iter_modules(__path__, f"{__package__}.")]

