Mantid Imaging next release
===========================

This contains changes for the next not yet released Mantid Imaging versions.

New Features and improvements
-----------------------------

- #1601 : arithmetic filter optimisation
- #1616 : Change selected stack with single click on tree widget
- #1625 : Allow adding extra stacks to a dataset

Fixes
-----
- #1589 : Recommend new update command
- #1330 : Initial ROI box is sometimes much larger than image for relevant filters
- #1602 : Prevent multiple ROI selector windows opening from Operations window
- #1610 : Apply bug fix to disable Spectrum Viewer export button when no data is loaded

Developer Changes
-----------------
- #1472 : Investigate issues reported by flake8-bugbear
- #1607 : Add flake8-bugbear to environment, github actions and precommit
- #1613 : Refactor Operations window ROI selector to be in its own class