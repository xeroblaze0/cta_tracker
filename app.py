from flask import Flask, render_template
from cta_tracker import create_map

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/map')
def map_data():
    m = create_map()
    return m._repr_html_()

if __name__ == '__main__':
    app.run(debug=True, port=5002)
