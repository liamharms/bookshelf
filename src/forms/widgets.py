from wtforms import SelectField
from markupsafe import Markup

class SelectTree:

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('name', field.name)

        selected_value = kwargs.pop('value', field.data or '')

        # Build HTML
        html = [f'<div class="select-tree-container">']

        # Search input
        html.append(f'''
            <input type="text" 
                   class="form-control mb-2" 
                   id="{field.id}_search" 
                   placeholder="Search locations..."
                   onkeyup="filterLocations_{field.id}(this.value)">
        ''')

        # Hidden input to store the actual value
        html.append(f'''
            <input type="hidden" 
                   id="{kwargs['id']}" 
                   name="{kwargs['name']}" 
                   value="{selected_value}">
        ''')

        # Tree
        html.append(f'<div class="select-tree" id="{field.id}_tree">')
        html.append('<ul class="tree-list">')

        html.append(self._render_tree(field.choices, selected_value, field.id))
        
        html.append('</ul>')
        html.append('</div>')
    
    def _render_tree(self, choices, selected_value, field_id, level=0):
        pass