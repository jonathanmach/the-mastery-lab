# Mermaid ER Diagram Viewer

A small browser-based viewer for Mermaid `erDiagram` schemas. Paste or edit Mermaid source, apply it to render draggable entity cards and relationship connectors, and reset the layout at any time.

## Run locally

```sh
npm install
npm run dev
```

## First-version scope

- Parses Mermaid entity declarations, attributes, key markers, quoted attribute comments, and labeled relationships.
- Supports `%% @relate-group Group name: entity, entity` comment directives to visually group and initially cluster entities without changing Mermaid ER diagram syntax.
- Persists entity and group canvas positions in `%% @relate-position entity: x, y` comments when cards or groups are dragged; editing only these directives updates the canvas immediately, and resetting the layout removes the overrides.
- Validates supported ER diagram syntax before replacing the currently displayed diagram.
- Drag entities or a group frame to rearrange them; connector paths and group outlines follow their contents.
- Pan the canvas with two-finger trackpad scrolling or toggle the hand tool to click-drag the view.
- Zoom with the toolbar or macOS trackpad pinch gesture; the diagram centers in the viewport when it fits, including at the 25% minimum zoom, with pannable canvas around it at any zoom.
- Position directives are written into the Mermaid source so they can be copied and reused; the prototype does not save the diagram source across page reloads.
- The source-panel visibility preference is saved locally.

Group and position directives are viewer metadata in Mermaid comments. Mermaid renderers that do not know the `@relate-group` and `@relate-position` conventions ignore them and continue to render the ER diagram as usual. Each entity can belong to only one group; entities omitted from group directives remain ungrouped. Entities without saved positions use the automatic layout.
