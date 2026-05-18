<img width="473" height="517" alt="image" src="https://github.com/user-attachments/assets/907f92a0-1d47-49aa-802d-23f4afd84d2e" />

# Create On Selection

A Maya Python tool that creates joints, locators, or nulls directly from your selection.

Placement Methods:
- Bounding Box    : Creates at the center of each selected polygon mesh
- Each Position   : Creates at each selected vertex, edge, or face center
- Edge Length     : Distributes evenly along selected edges by arc length
- Curve CV        : Places at every CV point on a selected NURBS curve
- Curve Length    : Distributes evenly along a curve based on actual arc length

Naming  : Custom naming with # for numbers (1,2,3...) and @ for alphabets (A,B,C...)<br/>
Division: Controls the number of objects created along edges or curves<br/>
Chain   : Builds a parent hierarchy between created objects<br/>
Reverse : Reverses the creation order<br/>

## Usage
Run the script in Maya's Script Editor or add to a shelf button.

## Requirements
- Autodesk Maya (Python 3)
