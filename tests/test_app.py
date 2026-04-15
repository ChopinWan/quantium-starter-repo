from dash import dcc, html

from app import create_app


def _walk_components(component):
    """Yield every component in the Dash layout tree."""
    yield component
    children = getattr(component, "children", None)

    if children is None:
        return

    if isinstance(children, (list, tuple)):
        for child in children:
            if child is not None:
                yield from _walk_components(child)
    else:
        yield from _walk_components(children)


def test_header_is_present():
    app = create_app()
    header = next(
        (
            component
            for component in _walk_components(app.layout)
            if isinstance(component, html.H1)
        ),
        None,
    )

    assert header is not None
    assert "Pink Morsel Sales Explorer" in str(header.children)


def test_visualisation_is_present():
    app = create_app()
    graph = next(
        (
            component
            for component in _walk_components(app.layout)
            if isinstance(component, dcc.Graph) and component.id == "sales-line-chart"
        ),
        None,
    )

    assert graph is not None


def test_region_picker_is_present():
    app = create_app()
    picker = next(
        (
            component
            for component in _walk_components(app.layout)
            if isinstance(component, dcc.RadioItems) and component.id == "region-filter"
        ),
        None,
    )

    assert picker is not None

    option_values = {option["value"] for option in picker.options}
    assert option_values == {"all", "north", "east", "south", "west"}
