# -*- coding: utf-8 -*-
from pwn import *
import json
import tornado.ioloop
import tornado.web
import tornado.websocket
import thread
import time
import copy

# up = 0
# down = 1
# left = 2
# right = 3
dx = [-1, 1, 0, 0]
dy = [0, 0, -1, 1]
direction = -1
map_size = 99
x, y = 0, 0
inf = 1e9
res = 0
safe_weight = 5#xxx_weigth为xxx的权重
socre_weight = 5
explore_weight = 5
view_weight = 10
std_score = 5.0#stx_xxx为xxx的标准分
std_safe = 30.0
std_view = 10.0
values = [0 for i in range(260)]
derictions = ["w", "s", "a", "d"]

Blank = 0
Blocks = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15]
Block = 1
# Shoes=2
Scope = 3
Shit = 4
Food = 5
BigFood = 6
Head = 12
Body = 8
Unknow = 255

ui_client = []

game_map = [[Unknow for j in range(99)]for i in range(99)]


def init_values():
    global values
    values[Block] = -3
    values[Shit] = 0
    values[Blank] = 1
    values[Scope] = 2
    values[Unknow] = 2
    values[Food] = 3
    values[BigFood] = 5


def dfs(x, y):
    global res
    if x >= map_size or y >= map_size:
        return
    if(game_map[x][y] == Unknow):
        res += 10
        print("reach_Unknow")
        return
    res += 1
    if(res >= 200):
        return
    game_map[x][y] = Body
    for i in range(4):
        nx = x+dx[i]
        ny = y+dy[i]
        if(game_map[nx][ny] in Blocks):
            continue
        dfs(nx, ny)
        if(res >= 25):
            return


def decition():
    global res, game_map
    mx = -inf
    ret = "w"
    tmp = copy.deepcopy(game_map)
    for i in range(4):
        safe_value = 0  # safe_value计算了当前决策的安全程度
        score_value = 0  # score_value，或者说短视估值，目前的策略是只看下一步能吃到啥，不是很理想（或许可以改成蛇头相邻的U形区域内五个格子的权值和？
        explore_value = 0  # 探索估值，决定了蛇探索Unknown的欲望
        view_value = 0  # 远视估值，目前的策略是计算9*9区域内的价值和，不是很理想
        nx = x+dx[i]
        ny = y+dy[i]
        print(nx, ny, game_map[nx][ny])
        score_value = values[game_map[nx][ny]]/std_score*socre_weight

        if(game_map[nx][ny] in Blocks):
            safe_value = -inf
        else:
            res = 0
            dfs(nx, ny)
            game_map = copy.deepcopy(tmp)
            # print("fuck")
            if(res) <= 15:
                safe_value = -inf
            else:
                safe_value = (res/std_safe)*safe_weight
        for j in range(nx-4, nx+5):
            for k in range(ny-4, ny+5):
                if k >= map_size or j >= map_size:
                    continue
                if game_map[j][k] in Blocks and game_map[j][k] != Unknow:
                    view_value += values[Block]
                else:
                    view_value += values[game_map[j][k]]
                if game_map[j][k] == Unknow:
                    explore_value += 1
        explore_value = explore_value/9.0*explore_weight
        view_value = view_value/std_view*view_weight
        sum_value = safe_value+score_value+explore_value+view_value
        print derictions[i], sum_value
        if sum_value > mx:
            mx = sum_value
            ret = derictions[i]
    return ret


class GameUI(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        """
        客户端连接成功时，自动执行
        :return: 
        """
        ui_client.append(self)
        print("fuck")
        pass

    def on_message(self, message):
        """
        客户端连发送消息时，自动执行
        :param message: 
        :return: 
        """
        pass

    def on_close(self):
        """
        客户端关闭连接时，，自动执行
        :return: 
        """
        pass

    @classmethod
    def draw(cls, map_json):
        ui_client[0].write_message(map_json)


def run_ui():
    ui = tornado.web.Application([
        (r"/", GameUI),
    ])
    ui.listen(9961)
    tornado.ioloop.IOLoop.instance().start()


def find_head():
    rx, ry = 0, 0
    for row in view:
        ry = 0
        for i in row:
            if i == Head:
                return rx, ry
            ry += 1
        rx += 1


if __name__ == "__main__":
    thread.start_new_thread(run_ui, ())
    l = listen(8080)
    # r = remote('localhost', l.lport)
    c = l.wait_for_connection()
    init_values()
    while(True):
        view = c.recvuntil("}")
        view = json.loads(view)
        # print(view)
        # c.send("d")
        x, y = view["x"], view["y"]
        view = view["view"]
        tmp = view
        n = len(view)
        m = len(view[0])
        rx, ry = find_head()
        for i in range(n):
            for j in range(m):
                game_map[x-rx+i][y-ry+j] = view[i][j]

        for i in range(x-4, x+5):
            for j in range(y-4, y+5):
                if i >= map_size or j >= map_size:
                    continue
                print game_map[i][j],
            print '\n',
        GameUI.draw(json.dumps({"map": game_map}))
        time.sleep(0.1)
        # raw_input()
        direction = decition()
        # direction="s"
        c.send(direction)
        print(direction)
        # print(json.dumps({"map":game_map}))
