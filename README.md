### Introduction
This repo services a Streamlit app for guessing where random pro athletes played in college.
<br>**Try it out here:** https://wheredidtheyball.streamlit.app

<img width="756" height="365" alt="image" src="https://github.com/user-attachments/assets/9e37e890-a17e-4afc-97fd-394b945cf1b6" />


### Data
Data powering the app comes directly from the ESPN API. Transfer data is not currently captured within the project, so the most recent college a player played at is usually the correct answer. 
<br><strong>Example:</strong> A player like Riley Leonard who transferred from Duke to Notre Dame, the app will show Notre Dame as the correct answer.

### App Usage
Players are chosen completely at random. Use the Sport and Position filters to narrow down the player pool (ie. NFL Wide Receivers, NBA Centers). Use the Player Status filter to pick from a pool of only active players or from all players (active, practice squad, retired, etc). The app keeps track of your score as you play at the bottom. Since the guess form is manual text input, I have built in a challenge flag feature that adds 1 to your score if you believe your last answer was correct or a typo. I have also built out an accepted answers database that should handle most common naming conventions for a school (Southern Cal, USC, etc).

### Future Roadmap
- Daily Game 
- Include Transfers
- Automate ELT Pipeline
