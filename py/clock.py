import os
import sys
import argparse
import datetime
import decimal
import pygame
from typing import Any

def render_time(time: datetime.datetime, font: pygame.font.Font, chars_size: dict, args: argparse.Namespace) -> pygame.Surface:
    surface = pygame.Surface(chars_size['size'])
    surface.fill(args.background)
    x = 0
    fmt = '%I' if args.halfday else '%H'
    fmt += ':%M:%S'
    if args.subseconds > 0:
        fmt += '.%f'
    text = time.strftime(fmt)
    if args.subseconds > 0:
        text = text[:-6+args.subseconds]
    if not args.zeropadded and text[0] == '0':
        text = ' ' + text[1:]
    dy = chars_size['height']
    for c in text:
        font_surface = font.render(c, args.antialias, args.color)
        dx = chars_size['digit'] if c.isdigit() else chars_size.get(c, font_surface.get_width())
        char_size = (dx, dy)
        coor = [x, 0]
        if c == ':':
            for i, v in enumerate(coor):
                if chars_size['colon_offset'][i].as_tuple().exponent == 0:
                    coor[i] += int(chars_size['colon_offset'][i])
                else:
                    coor[i] += int(chars_size['colon_offset'][i] * char_size[i])
        surface.blit(font_surface, coor)
        x += dx
    return surface

class limited_int(object):
    def __init__(self, lo: int, hi: int) -> None:
        self._lo = lo
        self._hi = hi
    def __call__(self, v: Any) -> int:
        v = int(v)
        if v < self._lo:
            raise ValueError(f'Argument has to be equal or higher than {self._lo}, but {v} passed.')
        if v > self._hi:
            raise ValueError(f'Argument has to be equal or lower than {self._hi}, but {v} passed.')
        return v

def main(argv):
    if len(argv) <= 1:
        argv = 'clock.py -d 1 -t 12:59:57 -T 12:59:59 -H -S 2 -c grey'.split()
    default_time = datetime.datetime.now()
    parser = argparse.ArgumentParser(os.path.splitext(os.path.basename(argv[0]))[0])
    parser.add_argument('-t', '--time', type=datetime.time.fromisoformat, default=default_time)
    parser.add_argument('-T', '--stoptime', type=datetime.time.fromisoformat, action='append')
    parser.add_argument('-w', '--window', action='store_false', dest='fullscreen')
    parser.add_argument('-d', '--display', type=int, default=0)
    parser.add_argument('-f', '--font')
    parser.add_argument('-b', '--bold', action='store_true')
    parser.add_argument('-i', '--italic', action='store_true')
    parser.add_argument('-u', '--underline', action='store_true')
    parser.add_argument('-s', '--stirke', action='store_true')
    parser.add_argument('-a', '--antialias', action='store_true')
    parser.add_argument('-c', '--color', type=pygame.Color, default='blue')
    parser.add_argument('-g', '--background', type=pygame.Color, default='black')
    parser.add_argument('-S', '--subseconds', type=limited_int(0, 6), default=3)
    parser.add_argument('-H', '--halfday', action='store_true')
    parser.add_argument('-z', '--zeropadded', action='store_true')
    parser.add_argument('--colonx', type=decimal.Decimal, default='0')
    parser.add_argument('--colony', type=decimal.Decimal, default='0')
    args = parser.parse_args(argv[1:])
    if isinstance(args.time, datetime.time):
        args.time = datetime.datetime.combine(datetime.datetime.today(), args.time)
    for i, t in enumerate(args.stoptime):
        if isinstance(t, datetime.time):
            args.stoptime[i] = datetime.datetime.combine(datetime.datetime.today(), t)
    pygame.init()
    clock = pygame.time.Clock()
    clock.tick()
    time = args.time
    if time == default_time:
        time = datetime.datetime.now()
    resolutions = pygame.display.get_desktop_sizes()
    screen = pygame.display.set_mode(flags=pygame.FULLSCREEN if args.fullscreen else pygame.RESIZABLE, display=args.display % len(resolutions))
    screen_size = screen.get_size()
    status_font = pygame.font.SysFont('system', 24)
    status_color = pygame.Color('white') - args.background
    speed = 1 # 0.000155551 is effectivelly stopped, 0.000171106 still running
    speed_coef = 1.1
    chars_size = {}
    redraw = False
    start_time = False
    pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, size = screen_size, w = screen_size[0], h = screen_size[1]))
    while True:
        e = pygame.event.poll()
        if e.type == pygame.NOEVENT:
            pass
        elif e.type == pygame.QUIT:
            break
        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                break
            if e.key == pygame.K_SPACE:
                start_time = True
        elif e.type == pygame.MOUSEWHEEL:
            if e.y > 0:
                speed *= e.y * speed_coef
            elif e.y < 0:
                speed /= -e.y * speed_coef
        elif e.type == pygame.VIDEORESIZE:
            screen_size = e.size
            if True: #args.font != None: # For future implementation of custom 7segment display
                size = 1
                over_size = None
                if args.font != None: # this condition (not the body) can be removed when rendered 7segment font will be implemented
                    sysfont = not os.path.isfile(args.font)
                    if sysfont:
                        font_file = pygame.font.match_font(args.font, args.bold, args.italic)
                        if font_file != None:
                            print(f'Using system font {os.path.split(font_file)[-1]}')
                        else:
                            print(f'Using default system font {pygame.font.get_default_font()}')
                    else:
                        print(f'Using custom font {args.font}')
                else:
                    print(f'Using default system font {pygame.font.get_default_font()}')
                    sysfont = True
                while True:
                    if sysfont:
                        font = pygame.font.SysFont(args.font, size, args.bold, args.italic)
                    else:
                        font = pygame.font.Font(args.font, size)
                        font.bold = args.bold
                        font.italic = args.italic
                    widest_digit = (0, 0)
                    for i in range(10):
                        w = font.size(str(i))[0]
                        if w > widest_digit[1]:
                            widest_digit = (i, w)
                    widest_number = (0, 0)
                    for i in range(100):
                        t = f'{i:02}'
                        w = font.size(t)[0]
                        if w > widest_number[1]:
                            widest_number = (i, w)
                    chars_size['digit'] = widest_digit[1] if (2 * widest_digit[1] > widest_number[1]) else ((widest_number[1] + 1) // 2)
                    for c in ':.':
                        chars_size[c] = font.size(c)[0]
                    chars_size[' '] = chars_size['digit']
                    chars_size['width'] = (3*2+args.subseconds)*chars_size['digit'] + 2*chars_size[':'] + (chars_size['.'] if args.subseconds > 0 else 0)
                    chars_size['height'] = font.get_linesize()
                    chars_size['size'] = (chars_size['width'], chars_size['height'])
                    if chars_size['size'] <= screen_size:
                        under_size = size
                        if over_size:
                            used_font = font
                            used_size = chars_size
                            if (over_size - under_size) < 2:
                                break
                            size = (under_size + over_size) // 2
                        else:
                            size *= 2
                    else:
                        over_size = size
                        if (over_size - under_size) < 2:
                            break
                        size = (under_size + over_size) // 2
                font = used_font
                chars_size = used_size
                chars_size['colon_offset'] = (args.colonx, args.colony)
            else:
                font = None
                chars_size = screen_size
            redraw = True
        else:
            pass
        if redraw:
            dt = clock.tick()
            dt = datetime.timedelta(milliseconds=dt)
            new_time = time + dt * speed
            if start_time:
                time = new_time
                start_time = False
            else:
                for t in args.stoptime:
                    if time <= t and new_time >= t:
                        time = t
                        break
                else:
                    time = new_time
            screen.fill(args.background)
            fake_time = time
            real_time = datetime.datetime.now()
            fake_time = render_time(fake_time, font, chars_size, args)
            real_time = render_time(real_time, font, chars_size, args)
            #time_delta = font.render(f'{time_delta.seconds + time_delta.days * 86400 + (1 if time_delta.days < 0 else 0):3}.{(1000000 - time_delta.microseconds) if time_delta.days < 0 else time_delta.microseconds:06}', args.antialias, args.color, args.background)
            y = 0
            screen.blit(fake_time, (0, y))
            y += fake_time.get_height()
            screen.blit(real_time, (0, y))
            status = status_font.render(f'speed {speed:13.9f}; {clock.get_fps():.1f} FPS', False, status_color, args.background)
            screen.blit(status, pygame.Vector2(screen_size) - pygame.Vector2(status.get_size()))
            pygame.display.flip()
    pygame.quit()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))