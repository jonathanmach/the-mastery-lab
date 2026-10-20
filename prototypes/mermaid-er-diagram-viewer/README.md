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
- Validates supported ER diagram syntax before replacing the currently displayed diagram.
- Drag entities or a group frame to rearrange them; connector paths and group outlines follow their contents.
- Pan the canvas with two-finger trackpad scrolling or toggle the hand tool to click-drag the view.
- Zoom with the toolbar or macOS trackpad pinch gesture; the diagram centers in the viewport when it fits, including at the 25% minimum zoom, with pannable canvas around it at any zoom.
- Layout edits are currently in-memory and reset when the page reloads; the source-panel visibility preference is saved locally.

Group directives are viewer metadata in Mermaid comments. Mermaid renderers that do not know the `@relate-group` convention ignore them and continue to render the ER diagram as usual. Each entity can belong to only one group; entities omitted from directives remain ungrouped.
