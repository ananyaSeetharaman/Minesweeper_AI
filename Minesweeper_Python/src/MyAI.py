# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

from AI import AI
from Action import Action


class MyAI( AI ):

	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		# Basic game configuration
		self.rowDimension = rowDimension # number of rows on board
		self.colDimension = colDimension # number of columns on board
		self.totalMines = totalMines # number of mines on board for that specific game

		# First uncovered tile coordinates provided by the environment
		self.startX = startX # starting column of the first guaranteed safe tile
		self.startY = startY # starting row of the first guaranteed safe tile
		self.lastX = startX # initializes last move X to start tile's X
		self.lastY = startY # initializes last move Y to start tile's Y

		# Internal board state:
		# None  -> covered/unknown
		# 0..8  -> uncovered label
		# "M"   -> flagged mine (optional for later logic)
		self.board = [[None for _ in range(self.rowDimension)] for _ in range(self.colDimension)] # creates a 2D array of None values with rowDimension rows and colDimension columns

		self.coveredTiles = self.rowDimension * self.colDimension - 1 # counts the number of tiles that are covered after the first tile was already uncovered by the game
		self.uncoveredCount = 1 # tracks the number of tiles that have been uncovered by the game
		self.flaggedMines = set() # Empty set to track corrdinates that you can later mark as mines
		self.uncoveredTiles = {(startX, startY)} # Set of uncovered coordinates initilized with the starting tile
		self.frontier = set() # empty set for frontier logic

		# Action queue and leave condition helper
		self.safeMoves = [] # empty list or queue to store safe coordinates to move to next
		self.shouldLeaveAtCovered = self.totalMines # When the covered tiles left are mines, the agent should leave the game
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

		
	def getAction(self, number: int) -> "Action Object":

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		return Action(AI.Action.LEAVE)
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################
