P 1 0; down, v=v_{in}(t)
R1 1 2; right
R2 2 3; right
C1 2 4; up
C2 3 9; down
W 4 5; right
W 5 6; right
W 6 7; down, size=0
W 7 8; right, size=0.5
E 7 0 opamp 3 11; right, mirror
W 5 11; down, size=1
P 8 10; down, v=v_{out}(t)
W 0 9; right
W 9 10; right
;draw_nodes=connections, debug=True
;;\draw[help lines] (0,0) grid [xstep=0.1, ystep=0.1] (10,5);

