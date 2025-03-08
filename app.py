from flask import Flask, request, render_template, url_for
import os
from dotenv import load_dotenv
from groq import Groq
import json
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

app = Flask(__name__)

# Directory to save generated plots
app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/", methods=['GET', 'POST'])
def query_ai():
    
    if request.method == 'POST':
        # Loading in the evironment variables
        load_dotenv(override=True)
        
        prompt = request.form['sentence']

        # Create the Groq client
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"), )

        # Set the system prompt
        system_prompt = {
            "role": "system",
            "content":
            
            """
            Provide with very short answers.
            The answer should be a json object with three keys: lat, lon and name, 
            lon is the longitude of the coords for each match to the query
            lat is the latitude of the coords for each match to the query
            name is the name of the place
            
            only return 1 combination
            the answer should only contain the json object
            
            """
        }

        # Initialize the chat history
        chat_history = [system_prompt]

        chat_history.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(model="llama3-70b-8192",
                                                messages=chat_history,
                                                max_tokens=100,
                                                temperature=1.2)

        # Append the response to the chat history
        chat_history.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })
        
        try:
            json_dict = json.loads(response.choices[0].message.content)
        
            # Extract lon and lat
            longitudes = [json_dict['lon']]
            latitudes = [json_dict['lat']]
            
            # plotting onto the map
            fig = plt.figure(figsize=(10, 6))
            ax = plt.axes(projection=ccrs.PlateCarree())
            ax.set_global()

            # Add map features
            ax.coastlines()
            ax.add_feature(cfeature.BORDERS, linestyle=':')
            ax.add_feature(cfeature.LAND, edgecolor='black')
            ax.add_feature(cfeature.OCEAN, facecolor='lightblue')

            # Plot the points on the map
            plt.scatter(longitudes, latitudes, color='red', s=50, transform=ccrs.PlateCarree(), label='Locations')

            # Add title and legend
            plt.title('The location is: '+json_dict['name'])
            plt.legend()
            
            #Save the plot to a file
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'plot.png')
            plt.savefig(image_path)

            # Set the image URL to be displayed in the template
            image_url = url_for('static', filename='images/plot.png')
            
            return render_template('index.html', image_url=image_url, sentence=prompt)
        
        except json.JSONDecodeError:
            error_message = "Failed to parse JSON response."
            return render_template('index.html', image_url=None, error_message=error_message)
        except KeyError as e:
            error_message = f"Missing key in response: {e}."
            return render_template('index.html', image_url=None, error_message=error_message)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}."
            return render_template('index.html', image_url=None, error_message=error_message)
            
        
    return render_template('index.html', image_url=None)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=500)
