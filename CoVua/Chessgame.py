import os
import pygame
import sys
import time

def load_font(size, bold=False):
    candidates = ['Noto Sans', 'DejaVu Sans', 'Segoe UI', 'Arial']
    for name in candidates:
        path = pygame.font.match_font(name, bold=bold)
        if path:
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)

WIN_W  = 920          # Chiều rộng cửa sổ
WIN_H  = 720          # Chiều cao cửa sổ
SQ     = 76           # Kích thước mỗi ô cờ (pixel)
BSIZE  = 8            # Kích thước bàn cờ (8x8)
BPX    = BSIZE * SQ   # Chiều dài bàn cờ tính bằng pixel  (608)
BX     = 28           # Offset trái của bàn cờ
BY     = 52           # Offset trên của bàn cờ

WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
SQ_LIGHT    = (240, 217, 181)
SQ_DARK     = (181, 136,  99)
BG          = ( 28,  28,  44)   # Nền tối
PANEL       = ( 42,  42,  60)   # Khung thông tin bên phải
BTN_NORM    = ( 65, 125, 175)
BTN_HOVER   = ( 95, 158, 210)
BTN_RED     = (155,  55,  55)
BTN_GRAY    = ( 75,  75, 108)
BTN_GREEN   = ( 55, 130,  80)
ACCENT      = (110, 200, 120)   # Màu viền lượt đang đi

KING   = 'K'
QUEEN  = 'Q'
ROOK   = 'R'
BISHOP = 'B'
KNIGHT = 'N'
PAWN   = 'P'

WHITE_P = 'white'
BLACK_P = 'black'

SCR_START   = 'start'
SCR_TIME    = 'time'
SCR_PLAY    = 'play'
SCR_END     = 'end'

class Piece:
    

    def __init__(self, ptype: str, color: str, row: int, col: int):
        self.type      = ptype   # KING / QUEEN / ROOK / BISHOP / KNIGHT / PAWN
        self.color     = color   # WHITE_P hoặc BLACK_P
        self.row       = row
        self.col       = col
        self.has_moved = False   # Dùng để kiểm tra nhập thành và nước đầu tốt

    @property
    def symbol(self):
        
        return self.type

    def copy(self):
        p = Piece(self.type, self.color, self.row, self.col)
        p.has_moved = self.has_moved
        return p

    def __repr__(self):
        return f"{self.color[0].upper()}{self.type}({self.row},{self.col})"

class Board:
    

    def __init__(self):
        self.grid         = [[None] * 8 for _ in range(8)]
        self.en_passant_sq = None   # (row, col) hoặc None
        self._setup()

    def _setup(self):
        back = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for c in range(8):
            self.grid[0][c] = Piece(back[c], BLACK_P, 0, c)
            self.grid[1][c] = Piece(PAWN,    BLACK_P, 1, c)
            self.grid[6][c] = Piece(PAWN,    WHITE_P, 6, c)
            self.grid[7][c] = Piece(back[c], WHITE_P, 7, c)

    def get(self, row: int, col: int):
        
        if 0 <= row < 8 and 0 <= col < 8:
            return self.grid[row][col]
        return None

    def set(self, row: int, col: int, piece):
        
        self.grid[row][col] = piece
        if piece:
            piece.row = row
            piece.col = col

    def move(self, fr: int, fc: int, tr: int, tc: int):
        
        piece = self.grid[fr][fc]
        self.grid[tr][tc] = piece
        self.grid[fr][fc] = None
        if piece:
            piece.row      = tr
            piece.col      = tc
            piece.has_moved = True

    def find_king(self, color: str):
        
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p and p.type == KING and p.color == color:
                    return r, c
        return None

    def copy(self):
        b = Board.__new__(Board)
        b.grid          = [[None] * 8 for _ in range(8)]
        b.en_passant_sq = self.en_passant_sq
        for r in range(8):
            for c in range(8):
                p = self.grid[r][c]
                if p:
                    b.grid[r][c] = p.copy()
        return b

class Rules:
    

    @staticmethod
    def is_attacked(board: Board, row: int, col: int, by: str) -> bool:
        
        for r in range(8):
            for c in range(8):
                p = board.get(r, c)
                if not p or p.color != by:
                    continue

                if p.type == PAWN:
                    d = -1 if p.color == WHITE_P else 1   # hướng tấn công
                    if r + d == row and abs(c - col) == 1:
                        return True

                elif p.type == KING:
                    if abs(r - row) <= 1 and abs(c - col) <= 1 and (r, c) != (row, col):
                        return True

                elif p.type == KNIGHT:
                    dr, dc = abs(r - row), abs(c - col)
                    if {dr, dc} == {1, 2}:
                        return True

                if p.type in (BISHOP, QUEEN):
                    if abs(r - row) == abs(c - col) and r != row:
                        dr2 = 1 if row > r else -1
                        dc2 = 1 if col > c else -1
                        cr, cc = r + dr2, c + dc2
                        blocked = False
                        while (cr, cc) != (row, col):
                            if board.get(cr, cc):
                                blocked = True
                                break
                            cr += dr2
                            cc += dc2
                        if not blocked:
                            return True

                if p.type in (ROOK, QUEEN):
                    if r == row and c != col:
                        dc2 = 1 if col > c else -1
                        cc  = c + dc2
                        blocked = False
                        while cc != col:
                            if board.get(r, cc):
                                blocked = True
                                break
                            cc += dc2
                        if not blocked:
                            return True
                    elif c == col and r != row:
                        dr2 = 1 if row > r else -1
                        cr  = r + dr2
                        blocked = False
                        while cr != row:
                            if board.get(cr, c):
                                blocked = True
                                break
                            cr += dr2
                        if not blocked:
                            return True
        return False

    @staticmethod
    def in_check(board: Board, color: str) -> bool:
        pos = board.find_king(color)
        if not pos:
            return False
        enemy = BLACK_P if color == WHITE_P else WHITE_P
        return Rules.is_attacked(board, pos[0], pos[1], enemy)

    @staticmethod
    def raw_moves(board: Board, row: int, col: int):
        
        p = board.get(row, col)
        if not p:
            return []
        t, color = p.type, p.color

        if t == PAWN:   return Rules._pawn(board, row, col, color)
        if t == KNIGHT: return Rules._knight(board, row, col, color)
        if t == BISHOP: return Rules._slide(board, row, col, color, [(-1,-1),(-1,1),(1,-1),(1,1)])
        if t == ROOK:   return Rules._slide(board, row, col, color, [(-1,0),(1,0),(0,-1),(0,1)])
        if t == QUEEN:  return Rules._slide(board, row, col, color,
                                            [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)])
        if t == KING:   return Rules._king_basic(board, row, col, color)
        return []

    @staticmethod
    def _pawn(board, row, col, color):
        moves = []
        d  = -1 if color == WHITE_P else 1    # Trắng đi lên, Đen đi xuống
        sr =  6 if color == WHITE_P else 1    # Hàng xuất phát

        nr = row + d
        if 0 <= nr < 8 and board.get(nr, col) is None:
            moves.append((nr, col))
            if row == sr and board.get(row + 2*d, col) is None:
                moves.append((row + 2*d, col))

        for dc in (-1, 1):
            nc = col + dc
            nr = row + d
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board.get(nr, nc)
                if (target and target.color != color) or (nr, nc) == board.en_passant_sq:
                    moves.append((nr, nc))
        return moves

    @staticmethod
    def _knight(board, row, col, color):
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = row + dr, col + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                t = board.get(nr, nc)
                if not t or t.color != color:
                    moves.append((nr, nc))
        return moves

    @staticmethod
    def _slide(board, row, col, color, dirs):
        moves = []
        for dr, dc in dirs:
            nr, nc = row + dr, col + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                t = board.get(nr, nc)
                if t:
                    if t.color != color:
                        moves.append((nr, nc))   # ăn quân địch
                    break                         # bị chặn
                moves.append((nr, nc))
                nr += dr; nc += dc
        return moves

    @staticmethod
    def _king_basic(board, row, col, color):
        moves = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    t = board.get(nr, nc)
                    if not t or t.color != color:
                        moves.append((nr, nc))
        return moves

    @staticmethod
    def castling_moves(board: Board, row: int, col: int, color: str):
        
        moves = []
        king = board.get(row, col)
        if not king or king.has_moved:
            return moves

        enemy = BLACK_P if color == WHITE_P else WHITE_P

        if Rules.is_attacked(board, row, col, enemy):
            return moves

        rk = board.get(row, 7)
        if rk and rk.type == ROOK and not rk.has_moved:
            if board.get(row, 5) is None and board.get(row, 6) is None:
                if (not Rules.is_attacked(board, row, 5, enemy) and
                    not Rules.is_attacked(board, row, 6, enemy)):
                    moves.append((row, 6))

        rk = board.get(row, 0)
        if rk and rk.type == ROOK and not rk.has_moved:
            if (board.get(row, 1) is None and
                board.get(row, 2) is None and
                board.get(row, 3) is None):
                if (not Rules.is_attacked(board, row, 3, enemy) and
                    not Rules.is_attacked(board, row, 2, enemy)):
                    moves.append((row, 2))

        return moves

    @staticmethod
    def legal_moves(board: Board, row: int, col: int):
        
        piece = board.get(row, col)
        if not piece:
            return []

        candidates = Rules.raw_moves(board, row, col)

        if piece.type == KING:
            candidates += Rules.castling_moves(board, row, col, piece.color)

        legal = []
        for (tr, tc) in candidates:
            b2 = board.copy()

            if piece.type == PAWN and (tr, tc) == board.en_passant_sq:
                b2.grid[row][tc] = None

            if piece.type == KING and abs(tc - col) == 2:
                if tc == 6:    b2.move(row, 7, row, 5)   # cánh vua
                elif tc == 2:  b2.move(row, 0, row, 3)   # cánh hậu

            b2.move(row, col, tr, tc)

            if not Rules.in_check(b2, piece.color):
                legal.append((tr, tc))

        return legal

    @staticmethod
    def has_any_legal(board: Board, color: str) -> bool:
        
        for r in range(8):
            for c in range(8):
                p = board.get(r, c)
                if p and p.color == color:
                    if Rules.legal_moves(board, r, c):
                        return True
        return False

    @staticmethod
    def is_checkmate(board: Board, color: str) -> bool:
        
        return Rules.in_check(board, color) and not Rules.has_any_legal(board, color)

    @staticmethod
    def is_stalemate(board: Board, color: str) -> bool:
        
        return not Rules.in_check(board, color) and not Rules.has_any_legal(board, color)

class ChessGame:

    def __init__(self):
        pygame.init()
        self.win   = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("Co Vua - 2 Nguoi Choi")
        self.clock = pygame.time.Clock()

        self.f_xl  = load_font(54, bold=True)
        self.f_lg  = load_font(38, bold=True)
        self.f_md  = load_font(28, bold=True)
        self.f_sm  = load_font(20, bold=False)
        self.f_xs  = load_font(15, bold=False)
        self.f_pce = load_font(26, bold=True)

        self.piece_images = {}
        self._load_piece_images()

        self.screen = SCR_START

        self.board      = None
        self.turn       = WHITE_P
        self.sel        = None    # (row,col) ô đang chọn
        self.moves      = []      # nước đi hợp lệ của ô đang chọn
        self.paused     = False
        self.promo_sq   = None    # (row,col) tốt chờ phong cấp

        self.time_limit  = None   # số giây hoặc None
        self.white_secs  = 0.0
        self.black_secs  = 0.0
        self._last_tick  = 0.0

        self.game_over  = False
        self.winner     = None    # 'white' / 'black' / 'draw'
        self.over_msg   = ''

        self.log = []
    
    def _load_piece_images(self):
        self.piece_images = {}

        names = {
            (WHITE_P, PAWN): "white_pawn.png",
            (WHITE_P, ROOK): "white_rook.png",
            (WHITE_P, KNIGHT): "white_knight.png",
            (WHITE_P, BISHOP): "white_bishop.png",
            (WHITE_P, QUEEN): "white_queen.png",
            (WHITE_P, KING): "white_king.png",
            (BLACK_P, PAWN): "black_pawn.png",
            (BLACK_P, ROOK): "black_rook.png",
            (BLACK_P, KNIGHT): "black_knight.png",
            (BLACK_P, BISHOP): "black_bishop.png",
            (BLACK_P, QUEEN): "black_queen.png",
            (BLACK_P, KING): "black_king.png",
        }

        for key, filename in names.items():
            path = os.path.join("assets", filename)
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (SQ - 10, SQ - 10))
            self.piece_images[key] = img

    def new_game(self, time_limit):
        
        self.board       = Board()
        self.turn        = WHITE_P
        self.sel         = None
        self.moves       = []
        self.paused      = False
        self.promo_sq    = None
        self.time_limit  = time_limit
        self.white_secs  = float(time_limit) if time_limit else 0.0
        self.black_secs  = float(time_limit) if time_limit else 0.0
        self._last_tick  = time.time()
        self.game_over   = False
        self.winner      = None
        self.over_msg    = ''
        self.log         = []
        self.screen      = SCR_PLAY

    def _end(self, winner: str, msg: str):
        self.game_over = True
        self.winner    = winner
        self.over_msg  = msg
        self.screen    = SCR_END

    def _switch_turn(self):
        self.turn = BLACK_P if self.turn == WHITE_P else WHITE_P

    def tick_clock(self):
        
        if self.time_limit is None:
            return
        if self.game_over or self.paused or self.promo_sq:
            self._last_tick = time.time()
            return

        now   = time.time()
        delta = now - self._last_tick
        self._last_tick = now

        if self.turn == WHITE_P:
            self.white_secs = max(0.0, self.white_secs - delta)
            if self.white_secs == 0:
                self._end('black', 'Trắng hết giờ')
        else:
            self.black_secs = max(0.0, self.black_secs - delta)
            if self.black_secs == 0:
                self._end('white', 'Đen hết giờ')

    def on_board_click(self, mx: int, my: int):
        
        if self.game_over or self.promo_sq or self.paused:
            return

        col = (mx - BX) // SQ
        row = (my - BY) // SQ
        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board.get(row, col)

        if self.sel:
            sr, sc = self.sel
            if (row, col) in self.moves:
                self._do_move(sr, sc, row, col)
            elif piece and piece.color == self.turn:
                self.sel   = (row, col)
                self.moves = Rules.legal_moves(self.board, row, col)
            else:
                self.sel   = None
                self.moves = []
        else:
            if piece and piece.color == self.turn:
                self.sel   = (row, col)
                self.moves = Rules.legal_moves(self.board, row, col)

    def _do_move(self, fr: int, fc: int, tr: int, tc: int):
        
        piece = self.board.get(fr, fc)
        cap   = '×' if self.board.get(tr, tc) else ''

        self.log.append(
            f"{'W' if piece.color == WHITE_P else 'B'}"
            f"{piece.symbol}{cap}{chr(97+fc)}{8-fr}→{chr(97+tc)}{8-tr}"
        )

        if piece.type == PAWN and (tr, tc) == self.board.en_passant_sq:
            self.board.set(fr, tc, None)   # tốt bị bắt cùng hàng, cùng cột đích

        if piece.type == KING and abs(tc - fc) == 2:
            if tc == 6:    self.board.move(fr, 7, fr, 5)   # cánh vua
            elif tc == 2:  self.board.move(fr, 0, fr, 3)   # cánh hậu

        if piece.type == PAWN and abs(tr - fr) == 2:
            self.board.en_passant_sq = ((fr + tr) // 2, fc)
        else:
            self.board.en_passant_sq = None

        self.board.move(fr, fc, tr, tc)

        if piece.type == PAWN and (tr == 0 or tr == 7):
            self.promo_sq = (tr, tc)
            self.sel      = None
            self.moves    = []
            return   # Chờ người chơi chọn quân phong cấp

        self._after_move()

    def _after_move(self):
        
        self._switch_turn()
        self.sel   = None
        self.moves = []

        if Rules.is_checkmate(self.board, self.turn):
            w = 'white' if self.turn == BLACK_P else 'black'
            self._end(w, 'Chiếu hết!')
        elif Rules.is_stalemate(self.board, self.turn):
            self._end('draw', 'Hòa - Không còn nước đi')

    def on_promo_click(self, mx: int, my: int):
        
        if not self.promo_sq:
            return
        dw, dh = 348, 120
        dx = WIN_W // 2 - dw // 2
        dy = WIN_H // 2 - dh // 2
        choices = [QUEEN, ROOK, BISHOP, KNIGHT]

        for i, ptype in enumerate(choices):
            btn = pygame.Rect(dx + i * 86 + 6, dy + 34, 80, 70)
            if btn.collidepoint(mx, my):
                r, c  = self.promo_sq
                color = self.board.get(r, c).color
                new_p = Piece(ptype, color, r, c)
                new_p.has_moved = True
                self.board.set(r, c, new_p)
                self.promo_sq = None
                self._after_move()
                return

    def _txt(self, text, font, color, x, y, center=False):
        
        s = font.render(str(text), True, color)
        if center:
            x -= s.get_width()  // 2
            y -= s.get_height() // 2
        self.win.blit(s, (x, y))
        return s.get_rect(topleft=(x, y))

    def _btn(self, text, rect, hover=False, color=None, font=None):
        
        c = color if color else (BTN_HOVER if hover else BTN_NORM)
        pygame.draw.rect(self.win, c,              rect, border_radius=9)
        pygame.draw.rect(self.win, (200, 200, 220), rect, 2, border_radius=9)
        f = font or self.f_sm
        s = f.render(text, True, WHITE)
        self.win.blit(s, (rect.x + (rect.w - s.get_width())  // 2,
                          rect.y + (rect.h - s.get_height()) // 2))
        return rect

    def _overlay(self, x: int, y: int, rgba: tuple):
        
        s = pygame.Surface((SQ, SQ), pygame.SRCALPHA)
        s.fill(rgba)
        self.win.blit(s, (x, y))

    def _fmt(self, secs: float) -> str:
        
        s = max(0, int(secs))
        return f"{s//60:02d}:{s%60:02d}"

    def _draw_piece_at(self, piece, px, py):
        cx = px + SQ // 2
        cy = py + SQ // 2

        img = self.piece_images.get((piece.color, piece.type))
        if img is not None:
            rect = img.get_rect(center=(cx, cy))
            self.win.blit(img, rect)
            return

        r = SQ // 2 - 6
        if piece.color == WHITE_P:
            pygame.draw.circle(self.win, (245, 240, 225), (cx, cy), r)
            pygame.draw.circle(self.win, (90, 70, 50), (cx, cy), r, 2)
            tc = (40, 28, 18)
        else:
            pygame.draw.circle(self.win, (52, 47, 42), (cx, cy), r)
            pygame.draw.circle(self.win, (195, 175, 145), (cx, cy), r, 2)
            tc = (230, 215, 195)

        sym = self.f_pce.render(piece.symbol, True, tc)
        self.win.blit(sym, (cx - sym.get_width() // 2, cy - sym.get_height() // 2))

    def draw_start(self, mx, my):
        self.win.fill(BG)

        for r in range(5):
            for c in range(5):
                x = WIN_W // 2 - 80 + c * 32
                y = 230 + r * 32
                pygame.draw.rect(self.win, SQ_LIGHT if (r+c)%2==0 else SQ_DARK, (x,y,32,32))

        self._txt("CO VUA", self.f_xl, WHITE, WIN_W//2, 140, center=True)
        self._txt("2 Nguoi Choi", self.f_xs,
                  (170,170,200), WIN_W//2, 205, center=True)

        b_start = pygame.Rect(WIN_W//2 - 115, 400, 230, 60)
        b_quit  = pygame.Rect(WIN_W//2 - 115, 477, 230, 52)

        self._btn("BAT DAU", b_start, b_start.collidepoint(mx,my), color=BTN_GREEN, font=self.f_md)
        self._btn("THOAT GAME", b_quit,  b_quit.collidepoint(mx,my),  color=BTN_RED)

        self._txt("Nhap thanh, bat tot qua duong, phong cap",
                  self.f_xs, (120,120,150), WIN_W//2, 560, center=True)

        return b_start, b_quit

    def draw_time_select(self, mx, my):
        self.win.fill(BG)
        self._txt("Chon Thoi Gian Moi Nguoi", self.f_lg, WHITE, WIN_W//2, 130, center=True)
        self._txt("Chon gioi han thoi gian cho moi nguoi choi:",
                  self.f_xs, (175,175,205), WIN_W//2, 190, center=True)

        options = [
            ("10 Phut",       600),
            ("30 Phut",      1800),
            ("Khong gioi han", None),
        ]
        btns = []
        for i, (lbl, val) in enumerate(options):
            r = pygame.Rect(WIN_W//2 - 145, 240 + i*90, 290, 65)
            self._btn(lbl, r, r.collidepoint(mx,my), font=self.f_md)
            btns.append((r, val))

        b_back = pygame.Rect(WIN_W//2 - 105, 530, 210, 50)
        self._btn("Quay lai", b_back, b_back.collidepoint(mx,my), color=BTN_GRAY)

        return btns, b_back

    def draw_playing(self, mx, my):
        self.win.fill(BG)

        in_check = Rules.in_check(self.board, self.turn)
        king_sq  = self.board.find_king(self.turn) if in_check else None

        for r in range(8):
            for c in range(8):
                px = BX + c * SQ
                py = BY + r * SQ
                sq_color = SQ_LIGHT if (r+c) % 2 == 0 else SQ_DARK
                pygame.draw.rect(self.win, sq_color, (px, py, SQ, SQ))

                if self.sel == (r, c):
                    self._overlay(px, py, (90, 220, 90, 175))

                if (r, c) in self.moves:
                    target = self.board.get(r, c)
                    if target:
                        self._overlay(px, py, (220, 70, 70, 165))
                    else:
                        self._overlay(px, py, (90, 210, 90, 90))
                        cx2, cy2 = px + SQ//2, py + SQ//2
                        pygame.draw.circle(self.win, (55, 185, 55), (cx2, cy2), 11)

                if king_sq and (r, c) == king_sq:
                    self._overlay(px, py, (230, 45, 45, 200))

                p = self.board.get(r, c)
                if p:
                    self._draw_piece_at(p, px, py)

        for i in range(8):
            self._txt(chr(97+i), self.f_xs, (155,155,175),
                      BX + i*SQ + SQ//2 - 4, BY + BPX + 4)
            self._txt(str(8-i), self.f_xs, (155,155,175),
                      BX - 17, BY + i*SQ + SQ//2 - 8)

        PX = BX + BPX + 18
        PW = WIN_W - PX - 8

        def player_panel(top, color, secs, label):
            rect = pygame.Rect(PX, top, PW, 86)
            pygame.draw.rect(self.win, PANEL, rect, border_radius=8)
            border = ACCENT if self.turn == color else (65,65,90)
            pygame.draw.rect(self.win, border, rect, 2, border_radius=8)

            self._txt(label, self.f_sm, (210,210,215), PX+10, top+8)
            if self.time_limit is not None:
                tc2 = (255,85,85) if secs < 30 else (215,215,215)
                self._txt(self._fmt(secs), self.f_md, tc2, PX+10, top+40)
            else:
                if self.turn == color:
                    self._txt("◀ Đến lượt", self.f_xs, ACCENT, PX+10, top+50)

        player_panel(BY,            BLACK_P, self.black_secs, "  Đen")
        player_panel(BY+BPX-86,     WHITE_P, self.white_secs, "  Trắng")

        sp_y = BY + 96
        sp_h = BPX - 192
        sp   = pygame.Rect(PX, sp_y, PW, sp_h)
        pygame.draw.rect(self.win, PANEL, sp, border_radius=8)

        turn_str = "Trang" if self.turn == WHITE_P else "Den"
        self._txt(f"Luot: {turn_str}", self.f_sm, WHITE, PX+8, sp_y+8)

        if in_check:
            self._txt("DANG BI CHIEU!", self.f_sm, (255,85,85), PX+8, sp_y+34)

        ly = sp_y + 66
        self._txt("Lich su nuoc di:", self.f_xs, (135,135,165), PX+8, ly)
        ly += 19
        for entry in self.log[-12:]:
            self._txt(entry, self.f_xs, (195,195,215), PX+8, ly)
            ly += 17

        gear = pygame.Rect(WIN_W - 54, 8, 42, 42)
        pygame.draw.rect(self.win, PANEL, gear, border_radius=7)
        pygame.draw.rect(self.win, (180,180,200), gear, 2, border_radius=7)
        self._txt("SET", self.f_md, WHITE, gear.centerx, gear.centery, center=True)

        pause_btns = None
        if self.paused:
            pause_btns = self._draw_pause_menu(mx, my)

        if self.promo_sq:
            self._draw_promo_dialog(mx, my)

        return gear, pause_btns

    def _draw_pause_menu(self, mx, my):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 155))
        self.win.blit(ov, (0, 0))

        mw, mh = 310, 345
        mx2 = WIN_W // 2 - mw // 2
        my2 = WIN_H // 2 - mh // 2
        pygame.draw.rect(self.win, (36,36,55), (mx2,my2,mw,mh), border_radius=12)
        pygame.draw.rect(self.win, (195,195,215), (mx2,my2,mw,mh), 2, border_radius=12)
        self._txt("Menu", self.f_md, WHITE, mx2+mw//2, my2+14, center=True)

        items = [
            ("Tiep tuc",         'resume',  None),
            ("Choi lai",        'restart', None),
            ("Man hinh dau",'home',    BTN_GRAY),
            ("Thoat game",      'quit',    BTN_RED),
        ]
        btns = {}
        for i, (lbl, key, col) in enumerate(items):
            br = pygame.Rect(mx2+30, my2+65 + i*62, mw-60, 50)
            self._btn(lbl, br, br.collidepoint(mx, my), color=col)
            btns[key] = br
        return btns

    def _draw_promo_dialog(self, mx, my):
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 145))
        self.win.blit(ov, (0, 0))

        dw, dh = 356, 125
        dx = WIN_W // 2 - dw // 2
        dy = WIN_H // 2 - dh // 2
        pygame.draw.rect(self.win, (36,36,55), (dx,dy,dw,dh), border_radius=10)
        pygame.draw.rect(self.win, WHITE, (dx,dy,dw,dh), 2, border_radius=10)
        self._txt("Phong cap - Chon quan:", self.f_sm, WHITE, dx+dw//2, dy+8, center=True)

        r2, c2 = self.promo_sq
        color  = self.board.get(r2, c2).color
        choices = [QUEEN, ROOK, BISHOP, KNIGHT]

        for i, ptype in enumerate(choices):
            bx = dx + i*88 + 6
            by = dy + 34
            br = pygame.Rect(bx, by, 82, 74)
            hover = br.collidepoint(mx, my)
            pygame.draw.rect(self.win, (85,140,215) if hover else (58,98,162), br, border_radius=7)

            cx2, cy2 = bx+41, by+35
            pr = 24
            if color == WHITE_P:
                pygame.draw.circle(self.win, (245,240,225), (cx2,cy2), pr)
                pygame.draw.circle(self.win, (90,70,50),    (cx2,cy2), pr, 2)
                tc2 = (40,28,18)
            else:
                pygame.draw.circle(self.win, (52,47,42),    (cx2,cy2), pr)
                pygame.draw.circle(self.win, (195,175,145), (cx2,cy2), pr, 2)
                tc2 = (230,215,195)
            sym = self.f_pce.render(ptype, True, tc2)
            self.win.blit(sym, (cx2 - sym.get_width()//2, cy2 - sym.get_height()//2))

    def draw_ended(self, mx, my):
        self.win.fill(BG)

        for r in range(8):
            for c in range(8):
                px = BX + c*SQ
                py = BY + r*SQ
                pygame.draw.rect(self.win,
                    SQ_LIGHT if (r+c)%2==0 else SQ_DARK, (px, py, SQ, SQ))
        ov = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        ov.fill((28,28,44,200))
        self.win.blit(ov, (0,0))

        if self.winner == 'draw':
            title, tc2 = "  HÒA!",         (205,205,110)
        elif self.winner == 'white':
            title, tc2 = "  TRẮNG THẮNG!", (240,240,200)
        else:
            title, tc2 = "  ĐEN THẮNG!",  (165,165,255)

        self._txt(title,        self.f_xl, tc2, WIN_W//2, 185, center=True)
        self._txt(self.over_msg, self.f_sm, (170,170,200), WIN_W//2, 260, center=True)

        items = [
            ("Choi lai",          'restart', None),
            ("Man hinh dau",  'home',    BTN_GRAY),
            ("Thoat game",        'quit',    BTN_RED),
        ]
        btns = {}
        for i, (lbl, key, col) in enumerate(items):
            br = pygame.Rect(WIN_W//2-140, 320 + i*82, 280, 62)
            self._btn(lbl, br, br.collidepoint(mx,my), color=col, font=self.f_md)
            btns[key] = br
        return btns

    def run(self):
        running = True

        b_start = b_quit = None
        time_btns = b_back = None
        gear_r = pause_btns = None
        end_btns = None

        while running:
            mx, my = pygame.mouse.get_pos()

            if self.screen == SCR_PLAY and not self.game_over:
                self.tick_clock()

            if   self.screen == SCR_START:
                b_start, b_quit = self.draw_start(mx, my)

            elif self.screen == SCR_TIME:
                time_btns, b_back = self.draw_time_select(mx, my)

            elif self.screen == SCR_PLAY:
                gear_r, pause_btns = self.draw_playing(mx, my)

            elif self.screen == SCR_END:
                end_btns = self.draw_ended(mx, my)

            for event in pygame.event.get():

                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.screen == SCR_PLAY:
                        self.paused = not self.paused
                        self._last_tick = time.time()

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                    if self.screen == SCR_START:
                        if b_start and b_start.collidepoint(mx, my):
                            self.screen = SCR_TIME
                        elif b_quit and b_quit.collidepoint(mx, my):
                            running = False

                    elif self.screen == SCR_TIME:
                        clicked_time = False
                        if time_btns:
                            for btn, val in time_btns:
                                if btn.collidepoint(mx, my):
                                    self.new_game(val)
                                    clicked_time = True
                                    break
                        if not clicked_time and b_back and b_back.collidepoint(mx, my):
                            self.screen = SCR_START

                    elif self.screen == SCR_PLAY:

                        if gear_r and gear_r.collidepoint(mx, my):
                            self.paused = not self.paused
                            self._last_tick = time.time()

                        elif self.paused and pause_btns:
                            if pause_btns['resume'].collidepoint(mx, my):
                                self.paused = False
                                self._last_tick = time.time()
                            elif pause_btns['restart'].collidepoint(mx, my):
                                self.new_game(self.time_limit)
                            elif pause_btns['home'].collidepoint(mx, my):
                                self.paused = False
                                self.screen = SCR_START
                            elif pause_btns['quit'].collidepoint(mx, my):
                                running = False

                        elif self.promo_sq:
                            self.on_promo_click(mx, my)

                        else:
                            self.on_board_click(mx, my)

                    elif self.screen == SCR_END and end_btns:
                        if end_btns['restart'].collidepoint(mx, my):
                            self.new_game(self.time_limit)
                        elif end_btns['home'].collidepoint(mx, my):
                            self.screen = SCR_START
                        elif end_btns['quit'].collidepoint(mx, my):
                            running = False

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGame()
    game.run()
