import re

import hou


def ftrimify(parm):
    """Wrap an ftrim() function around channel refs.

    Args:
        parm (hou.Parm): Parameter to add ftrim()s to. Should be a
        hou.StringParmTemplate.
    """
    if not isinstance(parm.parmTemplate(), hou.StringParmTemplate):
        return
    pattern = r"((?<!ftrim\()(chs*\(.*?\)|@[^`]*))"
    repl = r"ftrim(\1)"
    raw = parm.rawValue()
    # Don't do anything if no match found
    if not re.findall(pattern, raw):
        return
    ftrimmed = re.sub(pattern, repl, raw)
    replace_parm(parm, ftrimmed)


def replace_parm(parm, repl):
    """Replace parms with or without exprs/refs in them.

    Sometimes hou.Parm.set doesn't work exactly as needed.

    Args:
        parm (hou.Parm): Parameter to replace.
        repl (str): Replacement string.
    """
    if parm.keyframes():
        expr_lang = parm.expressionLanguage()
        parm.deleteAllKeyframes()
        parm.setExpression(repl, expr_lang)
    else:
        # If the raw parm is just `chs("../some/parm")`
        # Houdini will set the referenced parm instead.
        parm.revertToDefaults()
        parm.set(repl)


def ftrimify_all(node):
    """Run ftrimify() on all string parameters on a node.

    Args:
        node (hou.Node): Node to run over.
    """
    if not node:
        return
    # A little redundant since ftrimify() checks
    str_parms = [
        parm for parm in node.parms()
        if isinstance(parm.parmTemplate(), hou.StringParmTemplate)
    ]
    for str_parm in str_parms:
        ftrimify(str_parm)
