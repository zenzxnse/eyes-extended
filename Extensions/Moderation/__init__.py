import pkgutil

MODERATION = [module.name for module in pkgutil.iter_modules(__path__, f"{__package__}.")]

