from houdinihelp.server import get_houdini_app
from bookish import flaskapp
app = get_houdini_app(config_file=config, use_houdini_path=False)
pages = flaskapp.get_wikipages(app)
indexer = flaskapp.get_indexer(app)
indexer.update(pages, clean=False)

