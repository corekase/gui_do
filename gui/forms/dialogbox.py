# given a rect and a list of button options and a message:
# display the message and a grid of the button list items, wait for a selection
# and return a signal for which selection
#
# two kinds of dialog boxes, blocking and non-blocking
# non-blocking displays the dialog box window and it operates with other widgets
# until a selection in it is made and then it unloads
#
# blocking dialog box in the gui manager dims the entire screen to 50% brightness
# except for the dialog box and no other gui controls or widgets process until a
# dialog selection is made. it is a state for the gui manager and client processing,
# drawing, and undrawing proceeds as normal under the dialog state. the blocking
# dialog box may be moved around the dimmed screen
