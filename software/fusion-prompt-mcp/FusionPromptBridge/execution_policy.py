"""Strict read-only batch grammar. This is a small query language, not a Python sandbox."""
import ast

READ_METHODS = {'inspect', 'validate', 'minimum_distance', 'interference', 'capture', 'present', 'audit_hygiene','evidence_fingerprint','verify_engineering','reconcile_edit','reconcile_authoring'}


def validate_read_only(tree,methods=None):
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):
        raise ValueError('read_only requires only def run(ctx): return <queries>')
    fn=tree.body[0]; args=fn.args
    if (fn.name!='run' or fn.decorator_list or fn.returns or getattr(fn,'type_params',[]) or
        len(args.args)!=1 or args.args[0].arg!='ctx' or args.args[0].annotation or
        args.defaults or args.kw_defaults or args.kwonlyargs or args.posonlyargs or
        args.vararg or args.kwarg or len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return)):
        raise ValueError('read_only requires only def run(ctx): return <queries>')
    def literal(node):
        try: ast.literal_eval(node)
        except (ValueError,TypeError,SyntaxError): raise ValueError('Query arguments must be literals')
    def query(node):
        if isinstance(node,ast.Call):
            f=node.func
            if not (isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name) and
                    f.value.id=='ctx' and f.attr in (READ_METHODS if methods is None else methods)):
                raise ValueError('Only approved read-only ctx queries are allowed')
            for arg in node.args: literal(arg)
            for kw in node.keywords:
                if kw.arg is None: raise ValueError('Keyword unpacking is not allowed')
                literal(kw.value)
        elif isinstance(node,(ast.List,ast.Tuple)):
            for child in node.elts: query(child)
        elif isinstance(node,ast.Dict):
            for key,value in zip(node.keys,node.values):
                if key is None: raise ValueError('Dictionary unpacking is not allowed')
                literal(key); query(value)
        else: literal(node)
    query(fn.body[0].value)


def validate_reconciliation(tree):
    validate_read_only(tree,{'acknowledge_authoring'})
    result=tree.body[0].body[0].value
    if not isinstance(result,ast.Call):
        raise ValueError('reconcile requires exactly one literal ctx.acknowledge_authoring(...) call')
