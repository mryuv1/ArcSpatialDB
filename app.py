from flask import Flask, render_template_string, request
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)
DATABASE_URL = 'sqlite:///elements.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
metadata = MetaData()
elements_table = Table('elements', metadata, autoload_with=engine)
areas_table = Table('areas', metadata, autoload_with=engine)

HTML = '''
<!doctype html>
<title>Spatial Query</title>
<h2>Spatial Query</h2>
<form method="post">
  <label>Bottom Left (XMin/YMin): <input name="bottom_left" required></label><br>
  <label>Top Right (XMax/YMax): <input name="top_right" required></label><br>
  <input type="submit" value="Query">
</form>
{% if error %}
  <p style="color:red;">{{ error }}</p>
{% endif %}
{% if results is not none %}
  <h3>Results:</h3>
  {% if results %}
    <table border="1" cellpadding="5">
      <tr><th>Element Name</th><th>Directory</th><th>Area ID</th><th>Bottom Left (XMin, YMin)</th><th>Top Right (XMax, YMax)</th></tr>
      {% for row in results %}
        <tr>
          <td>{{ row['name'] }}</td>
          <td>{{ row['directory'] }}</td>
          <td>{{ row['area_id'] }}</td>
          <td>({{ row['xmin'] }}, {{ row['ymin'] }})</td>
          <td>({{ row['xmax'] }}, {{ row['ymax'] }})</td>
        </tr>
      {% endfor %}
    </table>
  {% else %}
    <p>No matching areas found.</p>
  {% endif %}
{% endif %}
'''

def parse_point(s):
    try:
        s = s.strip()
        if '/' in s:
            x_str, y_str = s.split('/')
        elif ',' in s:
            x_str, y_str = s.split(',')
        else:
            return None
        return float(x_str), float(y_str)
    except Exception:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    error = None
    if request.method == 'POST':
        bottom_left = parse_point(request.form['bottom_left'])
        top_right = parse_point(request.form['top_right'])
        if not bottom_left or not top_right:
            error = 'Invalid input format. Please use X/Y or X,Y for both points.'
        else:
            xmin, ymin = bottom_left
            xmax, ymax = top_right
            if xmin >= xmax or ymin >= ymax:
                error = 'Bottom Left must be southwest (smaller X and Y) of Top Right. Please check your input.'
            else:
                session = Session()
                # Query: area must overlap with the user rectangle
                query = areas_table.join(elements_table, areas_table.c.element_id == elements_table.c.id)
                sel = (
                    areas_table.select()
                    .with_only_columns([
                        areas_table.c.id.label('area_id'),
                        areas_table.c.xmin, areas_table.c.ymin, areas_table.c.xmax, areas_table.c.ymax,
                        elements_table.c.name, elements_table.c.directory
                    ])
                    .select_from(query)
                    .where(
                        (areas_table.c.xmin < xmax) &
                        (areas_table.c.xmax > xmin) &
                        (areas_table.c.ymin < ymax) &
                        (areas_table.c.ymax > ymin)
                    )
                )
                results = [dict(row) for row in session.execute(sel)]
                session.close()
    return render_template_string(HTML, results=results, error=error)

if __name__ == '__main__':
    app.run(debug=True) 