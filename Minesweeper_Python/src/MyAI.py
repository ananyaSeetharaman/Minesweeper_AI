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
		self.rowDimension = rowDimension  # number of rows on board
		self.colDimension = colDimension  # number of columns on board
		self.totalMines = totalMines  # number of mines on board for that specific game

		# First uncovered tile coordinates provided by the environment
		self.startX = startX  # starting column of the first guaranteed safe tile
		self.startY = startY  # starting row of the first guaranteed safe tile
		self.lastX = startX  # initializes last move X to start tile's X
		self.lastY = startY  # initializes last move Y to start tile's Y

		# Internal board state:
		# None  -> covered/unknown
		# 0..8  -> uncovered label
		# "M"   -> flagged mine (optional for later logic)
		self.board = [[None for _ in range(self.rowDimension)] for _ in range(
			self.colDimension)]  # creates a 2D array of None values with rowDimension rows and colDimension columns

		self.coveredTiles = self.rowDimension * self.colDimension - 1  # counts the number of tiles that are covered after the first tile was already uncovered by the game
		self.uncoveredCount = 1  # tracks the number of tiles that have been uncovered by the game
		self.flaggedMines = set()  # Empty set to track corrdinates that you can later mark as mines
		self.uncoveredTiles = {(startX, startY)}  # Set of uncovered coordinates initilized with the starting tile
		self.frontier = set()  # empty set for frontier logic

		# Action queue and leave condition helper
		self.safeMoves = []  # empty list or queue to store safe coordinates to move to next
		self.shouldLeaveAtCovered = self.totalMines  # When the covered tiles left are mines, the agent should leave the game
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################

	# =========================================================================
	# Helpers
	# =========================================================================

	def _inBounds(self, x, y):
		"""Return True if (x, y) is a valid board coordinate."""
		return 0 <= x < self.colDimension and 0 <= y < self.rowDimension

	def _neighbours(self, x, y):
		"""Yield all in-bounds (nx, ny) around (x, y)."""
		for dx in (-1, 0, 1):
			for dy in (-1, 0, 1):
				if dx == 0 and dy == 0:
					continue
				nx, ny = x + dx, y + dy
				if self._inBounds(nx, ny):
					yield nx, ny

	def _coveredNeighbours(self, x, y):
		"""Return list of covered, non-flagged neighbours."""
		return [
			(nx, ny) for nx, ny in self._neighbours(x, y)
			if self.board[nx][ny] is None  # None = covered & not flagged
		]

	def _flaggedNeighbours(self, x, y):
		"""Return list of flagged neighbours."""
		return [
			(nx, ny) for nx, ny in self._neighbours(x, y)
			if (nx, ny) in self.flaggedMines
		]

	def _effectiveLabel(self, x, y):
		"""Label minus the number of already-flagged neighbours."""
		return self.board[x][y] - len(self._flaggedNeighbours(x, y))

	def _freeCoveredCells(self):
		"""Return list of all covered, unflagged cells (board value is None)."""
		return [
			(x, y)
			for x in range(self.colDimension)
			for y in range(self.rowDimension)
			if self.board[x][y] is None
		]

	def _minesLeft(self):
		"""Unflagged mines remaining."""
		return self.totalMines - len(self.flaggedMines)

	# -------------------------------------------------------------------------
	#  Inference layer 1 — single-cell constraint rules
	# -------------------------------------------------------------------------

	def _inferCell(self, x, y):
		"""
        Apply the two classic rules for one revealed cell:
          • effective == 0          → every covered neighbour is safe
          • effective == #covered   → every covered neighbour is a mine
        Queues results into self.safeMoves / self.flaggedMines.
        """
		label = self.board[x][y]
		if label is None or not isinstance(label, int):
			return

		covered = self._coveredNeighbours(x, y)
		effective = self._effectiveLabel(x, y)

		if effective == 0:
			for cell in covered:
				if cell not in self.uncoveredTiles and cell not in self.safeMoves:
					self.safeMoves.append(cell)

		elif effective > 0 and effective == len(covered):
			for cell in covered:
				if cell not in self.flaggedMines:
					self.flaggedMines.add(cell)
					# Mark on internal board so _coveredNeighbours excludes it
					self.board[cell[0]][cell[1]] = "M"

	# -------------------------------------------------------------------------
	#  Inference layer 2 — subset / constraint-pair elimination
	# -------------------------------------------------------------------------

	def _inferSubsets(self):
		"""
        Collect frontier constraints and perform subset elimination.

        If constraint B's covered set ⊂ constraint A's covered set:
            diff_mines = eff_A − eff_B
            diff_cells = cov_A − cov_B
            diff_mines == 0         → diff_cells are all safe
            diff_mines == |diff|    → diff_cells are all mines
        """
		constraints = []
		for x in range(self.colDimension):
			for y in range(self.rowDimension):
				label = self.board[x][y]
				if label is None or not isinstance(label, int):
					continue
				cov = set(self._coveredNeighbours(x, y))
				if not cov:
					continue
				eff = self._effectiveLabel(x, y)
				constraints.append((eff, cov))

		for i, (eff_a, cov_a) in enumerate(constraints):
			for j, (eff_b, cov_b) in enumerate(constraints):
				if i == j:
					continue
				if cov_b < cov_a:  # B strict subset of A
					diff = cov_a - cov_b
					diff_mines = eff_a - eff_b
					if diff_mines == 0:
						for cell in diff:
							if cell not in self.uncoveredTiles and cell not in self.safeMoves:
								self.safeMoves.append(cell)
					elif diff_mines == len(diff):
						for cell in diff:
							if cell not in self.flaggedMines:
								self.flaggedMines.add(cell)
								self.board[cell[0]][cell[1]] = "M"

	# -------------------------------------------------------------------------
	#  Inference layer 3 — global mine-count reasoning
	# -------------------------------------------------------------------------

	def _inferGlobal(self):
		"""
        Use the total remaining mine count against all covered, unflagged cells.
          minesLeft == 0              → all remaining covered cells are safe
          minesLeft == #coveredFree   → all remaining covered cells are mines
        """
		minesLeft = self.totalMines - len(self.flaggedMines)
		free = [
			(x, y)
			for x in range(self.colDimension)
			for y in range(self.rowDimension)
			if self.board[x][y] is None
		]

		if minesLeft == 0:
			for cell in free:
				if cell not in self.uncoveredTiles and cell not in self.safeMoves:
					self.safeMoves.append(cell)
		elif minesLeft > 0 and minesLeft == len(free):
			for cell in free:
				if cell not in self.flaggedMines:
					self.flaggedMines.add(cell)
					self.board[cell[0]][cell[1]] = "M"

	# -------------------------------------------------------------------------
	#  Run all inference passes until the queues stabilise
	# -------------------------------------------------------------------------

	def _runInference(self):
		changed = True
		while changed:
			before = (len(self.safeMoves), len(self.flaggedMines))
			for x in range(self.colDimension):
				for y in range(self.rowDimension):
					self._inferCell(x, y)
			self._inferSubsets()
			self._inferGlobal()
			changed = (len(self.safeMoves), len(self.flaggedMines)) != before

	# -------------------------------------------------------------------------
	#  Probabilistic fallback — used only when inference is fully exhausted
	# -------------------------------------------------------------------------

	def _bestGuess(self):
		"""
        Estimate P(mine) for every free covered cell by blending the global
        mine rate with every local constraint that touches it. Return the
        cell with the lowest estimated probability.
        """
		free = [
			(x, y)
			for x in range(self.colDimension)
			for y in range(self.rowDimension)
			if self.board[x][y] is None
		]
		if not free:
			return None

		minesLeft = self.totalMines - len(self.flaggedMines)
		global_p = minesLeft / len(free)
		prob = {cell: global_p for cell in free}

		for x in range(self.colDimension):
			for y in range(self.rowDimension):
				label = self.board[x][y]
				if label is None or not isinstance(label, int):
					continue
				cov = self._coveredNeighbours(x, y)
				eff = self._effectiveLabel(x, y)
				if cov:
					local_p = max(0.0, min(1.0, eff / len(cov)))
					for cell in cov:
						if cell in prob:
							prob[cell] = (prob[cell] + local_p) / 2.0

		return min(prob, key=prob.get)

	def getAction(self, number: int) -> "Action Object":

		########################################################################
		#							YOUR CODE BEGINS						   #
		########################################################################
		x, y = self.lastX, self.lastY

		# ── 1. Record percept ────────────────────────────────────────────────
		# World sends number == -1 after FLAG / UNFLAG actions; skip recording.
		if number != -1:
			# Only record if this cell hasn't been logged yet
			if self.board[x][y] is None:
				self.board[x][y] = number
				self.uncoveredTiles.add((x, y))
				self.coveredTiles -= 1
				self.uncoveredCount += 1

		# ── 2. Run inference ─────────────────────────────────────────────────
		self._runInference()

		# ── 3. Termination check ─────────────────────────────────────────────
		# Leave when every remaining covered-and-unflagged cell is a mine.
		# We count directly from the board (None cells) so there's no lag
		# or off-by-one from coveredTiles tracking.
		free = self._freeCoveredCells()
		if len(free) <= self._minesLeft():
			return Action(AI.Action.LEAVE)

		# ── 4. Execute a FLAG if inference found a mine ───────────────────────
		# Find any flagged mine that hasn't been reported to the World yet.
		# We detect "not yet reported" by checking whether it still reads "M"
		# on our board but the World hasn't seen our FLAG action for it yet.
		# We maintain a separate set for this purpose.
		if not hasattr(self, '_reportedFlags'):
			self._reportedFlags = set()

		for cell in list(self.flaggedMines):
			if cell not in self._reportedFlags:
				self._reportedFlags.add(cell)
				self.lastX, self.lastY = cell
				return Action(AI.Action.FLAG, cell[0], cell[1])

		# ── 5. Execute a safe UNCOVER ─────────────────────────────────────────
		while self.safeMoves:
			cell = self.safeMoves.pop(0)
			cx, cy = cell
			if self.board[cx][cy] is None:  # still covered and not flagged
				self.lastX, self.lastY = cx, cy
				return Action(AI.Action.UNCOVER, cx, cy)

		# ── 6. Probabilistic fallback ─────────────────────────────────────────
		guess = self._bestGuess()
		if guess:
			self.lastX, self.lastY = guess
			return Action(AI.Action.UNCOVER, guess[0], guess[1])

		# ── 7. Nothing left to do ─────────────────────────────────────────────
		return Action(AI.Action.LEAVE)
		########################################################################
		#							YOUR CODE ENDS							   #
		########################################################################
