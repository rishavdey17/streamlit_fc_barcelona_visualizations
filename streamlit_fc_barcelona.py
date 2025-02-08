import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
from mplsoccer.pitch import Pitch, VerticalPitch
from natsort import natsorted

# App Title and Description
st.title("FC Barcelona 2024-25")
st.subheader("Passes, Actions & Heat Map of all Barça players in the match.")

# Define the root folder containing competitions
matches_folder = "Matches"

# Step 1: Get all competition names (sub-folders)
competitions = [folder for folder in os.listdir(matches_folder) if os.path.isdir(os.path.join(matches_folder, folder))]

if competitions:
    selected_competition = st.selectbox("Select Competition -", sorted(competitions))

    # Step 2: Get match files from the selected competition folder
    competition_path = os.path.join(matches_folder, selected_competition)
    match_files = glob.glob(os.path.join(competition_path, "*.csv"))  # List all CSV files

    if match_files:
        # Extract match names from filenames
        match_names = [os.path.basename(file).replace(".csv", "") for file in match_files]
        match_names = natsorted(match_names, reverse=True)  # Sort naturally
        
        # Step 3: Select a match
        selected_match = st.selectbox("Select A Match - ", match_names)
        
        # Step 4: Read the selected match file
        match_file_path = os.path.join(competition_path, f"{selected_match}.csv")
        df = pd.read_csv(match_file_path)
        df = df[df["teamName"] == "Barcelona"]

        # Extract end_x, end_y from qualifiers
        qualifier_id_cols = [col for col in df.columns if "/qualifierId" in col]
        qualifier_value_cols = [col.replace("/qualifierId", "/value") for col in qualifier_id_cols]

        df['end_x'] = np.nan
        df['end_y'] = np.nan

        for id_col, value_col in zip(qualifier_id_cols, qualifier_value_cols):
            df['end_x'] = df.apply(lambda row: row[value_col] if row[id_col] == 140 else row['end_x'], axis=1)
            df['end_y'] = df.apply(lambda row: row[value_col] if row[id_col] == 141 else row['end_y'], axis=1)

        # Check if "playerName" column exists
        if "playerName" in df.columns:
            # Step 5: Select a player from the match
            player_options = df["playerName"].dropna().astype(str).unique()
            selected_player = st.selectbox("Select Player -", sorted(player_options))

            # Display selected values
            st.write(f"**Selected Competition:** {selected_competition}")
            st.write(f"**Selected Match:** {selected_match}")
            st.write(f"**Selected Player:** {selected_player}")

            # Function to filter data
            def filter_data(df, player):
                return df[df['playerName'] == str(player)] if player else df

            # ✅ Filter data correctly
            filtered_data = filter_data(df, selected_player)

            # Create Pitch
            pitch = VerticalPitch(pitch_type='opta', pitch_color='black', line_color='white', linewidth=3, corner_arcs=True)
            fig, ax = pitch.draw(figsize=(10, 10), constrained_layout=True, tight_layout=False)
            fig.set_facecolor('black')

            # Function to plot actions on the pitch
            def plot_actions(df, ax, pitch):
                goal = df[df['typeId'] == 16]
                shot_miss = df[df['typeId'] == 13]
                shot_post = df[df['typeId'] == 14]
                shot_saved = df[df['typeId'] == 15]

                assist = df[df['assist'] == 1]
                chance = df[df['keyPass'] == 1]
                passes = df[df['typeId'] == 1]
                passes_successful = passes[(passes['outcome'] == 1) & ~(passes['eventId'].isin(chance['eventId']))]
                passes_unsuccessful = passes[passes['outcome'] == 0]

                recovery = df[df['typeId'] == 49]
                offside = df[df['typeId'] == 55]
                shield = df[df['typeId'] == 56]
                tackle = df[df['typeId'] == 7]
                succ_tackle = tackle[tackle['outcome'] == 1]

                interception = df[df['typeId'] == 8]
                block = df[df['typeId'] == 10]
                clearance = df[df['typeId'] == 12]

                foul = df[df['typeId'] == 4]
                foul_won = foul[foul['outcome'] == 1]
                foul_committed = foul[foul['outcome'] == 0]

                dribble = df[df['typeId'] == 3]
                succ_dribble = dribble[dribble['outcome'] == 1]

                aerial = df[df['typeId'] == 44]
                aerial_won = aerial[aerial['outcome'] == 1]
                aerial_lost = aerial[aerial['outcome'] == 0]

                dispossessed = df[df['typeId'] == 50]

                dribbled_past = df[df['typeId'] == 45]

                pickup = df[df['typeId'] == 52]
                punch = df[df['typeId'] == 41]

                # Convert necessary columns to float
                for df_subset in [assist, chance, passes, passes_successful, passes_unsuccessful]:
                    df_subset[['x', 'y', 'end_x', 'end_y']] = df_subset[['x', 'y', 'end_x', 'end_y']].astype(float)

                if selected_player in ["Wojciech Szczesny", "Inaki Pena", "Iñaki Peña", "Marc-Andre ter Stegen"]:
                    de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')
                    pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.6, headwidth=5, headlength=5, color='#00ff00', ax=ax, label='Successful Pass')
                    pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.6, headwidth=5, headlength=5, color='red', ax=ax, label='Unsuccessful Pass')
                    plt.scatter(block['y'], block['x'], s = 200, c = '#00ff00', marker = '*', edgecolor = '#000000', label ='Save')
                    plt.scatter(punch['y'], punch['x'], s = 100, c = '#ffec00', marker = 'o', edgecolor = '#000000', label = 'Punch')
                    plt.scatter(pickup['y'], pickup['x'], s = 120, c = '#dd571c', marker = 'P', edgecolor = '#000000', label = 'Pick-Up')
                    plt.scatter(recovery['y'], recovery['x'], s= 120, c = '#fcd200', marker = ',', edgecolor = '#000000', label = 'Ball Recovery')
                    plt.scatter(tackle['y'], tackle['x'], s= 120,c = 'cyan', marker = ',', edgecolor = '#000000', label = 'Tackle')
                    plt.scatter(interception['y'], interception['x'], s = 120, c = '#ff007f', marker = ',', edgecolor = '#000000', label = 'Interception')
                    plt.scatter(clearance['y'], clearance['x'], s = 100, c = '#9999ff', marker = 'x', edgecolor = '#000000', label = 'Clearance')
                    plt.scatter(offside['y'], offside['x'], s= 120, c = '#fcd200', marker = 'P', edgecolor = '#000000', label = 'Offside Provoked')
                    plt.scatter(shield['y'], shield['x'], s = 50, c = '#dd571c', marker = 'D', edgecolor = '#000000', label = 'Shielding Ball Out')
                    plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 200, c = '#fc3900', marker = '*', edgecolor = '#000000', label = 'Dribble')
                    plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                    plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                    plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')
                    plt.scatter(dribbled_past['y'], dribbled_past['x'], s = 50, c = '#cb0000', marker = 'x', edgecolor = '#000000', label = 'Dribbled Past')

                    ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.12), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')


                else:
                    # Plot player actions
                    de = pitch.kdeplot(passes.x, passes.y, ax=ax, shade=True, shade_lowest=False, alpha=0.4, n_levels=10, cmap='magma')

                    ax.scatter(goal['y'], goal['x'], s=120, c='#00ff00', edgecolor='#000000', label='Goal')
                    ax.scatter(shot_saved['y'], shot_saved['x'], s=120, c='#ff7c60', edgecolor='#000000', label='Saved/Blocked Shot')
                    ax.scatter(shot_post['y'], shot_post['x'], s=120, c='w', edgecolor='#000000', label='Shot Off Woodwork')
                    ax.scatter(shot_miss['y'], shot_miss['x'], s=120, c='r', edgecolor='#000000', label='Shot Off Target')

                    pitch.lines(assist.x, assist.y, assist.end_x, assist.end_y, color='#00ff00', comet = True, lw = 2.5, ax=ax, label='Assist')
                    ax.scatter(assist['end_y'], assist['end_x'], s=50, c='black', edgecolor='#00ff00')

                    pitch.lines(chance.x, chance.y, chance.end_x, chance.end_y, color='#ffea00', comet = True, lw = 2.5, ax=ax, label='Key Pass')
                    ax.scatter(chance['end_y'], chance['end_x'], s=50, c='black', edgecolor='#ffea00')

                    pitch.arrows(passes_successful.x, passes_successful.y, passes_successful.end_x, passes_successful.end_y, width=0.6, headwidth=5, headlength=5, color='#00ff00', ax=ax, label='Completed Pass')

                    pitch.arrows(passes_unsuccessful.x, passes_unsuccessful.y, passes_unsuccessful.end_x, passes_unsuccessful.end_y, width=0.6, headwidth=5, headlength=5, color='red', ax=ax, label='Incomplete Pass')

                    plt.scatter(succ_dribble['y'], succ_dribble['x'], s= 200, c = '#fc3900', marker = '*', edgecolor = '#000000', label = 'Dribble')
                    plt.scatter(recovery['y'], recovery['x'], s= 120, c = '#fcd200', marker = ',', edgecolor = '#000000', label = 'Ball Recovery')
                    plt.scatter(tackle['y'], tackle['x'], s= 120,c = 'cyan', marker = ',', edgecolor = '#000000', label = 'Tackle')
                    plt.scatter(block['y'], block['x'], s = 120, c = '#009afd', marker = ',', edgecolor = '#000000', label ='Block')
                    plt.scatter(interception['y'], interception['x'], s = 120, c = '#ff007f', marker = ',', edgecolor = '#000000', label = 'Interception')
                    plt.scatter(clearance['y'], clearance['x'], s = 100, c = '#9999ff', marker = 'x', edgecolor = '#000000', label = 'Clearance')
                    plt.scatter(offside['y'], offside['x'], s= 120, c = '#fcd200', marker = 'P', edgecolor = '#000000', label = 'Offside Provoked')
                    plt.scatter(shield['y'], shield['x'], s = 50, c = '#dd571c', marker = 'D', edgecolor = '#000000', label = 'Shielding Ball Out')
                    plt.scatter(foul_won['y'], foul_won['x'], s= 120, c = '#008000', marker = 'X', edgecolor = '#000000', label = 'Foul Won')
                    plt.scatter(foul_committed['y'], foul_committed['x'], s= 120, c = '#c21919', marker = 'X', edgecolor = '#000000', label = 'Foul Committed')
                    plt.scatter(aerial_won['y'], aerial_won['x'], s = 100, c = '#008000', marker = '^', edgecolor = '#000000', label = 'Aerial Won')
                    plt.scatter(aerial_lost['y'], aerial_lost['x'], s = 100, c = '#c21919', marker = '^', edgecolor = '#000000', label = 'Aerial Lost')
                    plt.scatter(dispossessed['y'], dispossessed['x'], s = 100, c = '#cb0000', marker = 'p', edgecolor = '#000000', label = 'Dispossessed')
                    plt.scatter(dribbled_past['y'], dribbled_past['x'], s = 50, c = '#cb0000', marker = 'x', edgecolor = '#000000', label = 'Dribbled Past')

                    ax.legend(loc='upper left', bbox_to_anchor=(-0.2, 1.18), facecolor = 'black', labelcolor = 'white', prop = {'size': 10}, framealpha=0.5, ncol=4, edgecolor='#ffffff')

            # ✅ Plot player actions
            plot_actions(filtered_data, ax, pitch)

            # ✅ Add footer
            endnote = "Made by Rishav. Data Source: OPTA. Built Using: Python and Streamlit."
            plt.figtext(0.53, 0.115, endnote, ha="center", va="top", fontsize=13, color="white")

            # ✅ Display plot in Streamlit
            st.pyplot(fig)
        else:
            st.warning("No data available for the selected player.")

    else:
        st.warning(f"No match files found in {selected_competition}.")
else:
    st.warning("No competitions found in the Matches folder.")
