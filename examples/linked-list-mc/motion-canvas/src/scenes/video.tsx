import {Line, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {Reference, all, createRef, sequence} from '@motion-canvas/core';
import {C, beat, finish, section} from '../kit';

const node = (ref: Reference<Rect>, x: number, y: number, v: string) =>
  <Rect ref={ref} x={x} y={y} width={140} height={100} radius={14} fill={C.panel} stroke={C.line} lineWidth={3}
    opacity={0}>
    <Txt text={v} fontFamily={C.font} fontWeight={700} fontSize={44} fill={C.fg}/>
  </Rect>;

export default makeScene2D(function* (view) {
  view.fill(C.bg);
  yield* section(view, 'll1');
  const xs = [-450, -50, 350];
  const nodes = xs.map(() => createRef<Rect>());
  xs.forEach((x, i) => view.add(node(nodes[i], x, 0, ['3', '7', '9'][i])));
  const arrows = [0, 1].map(() => createRef<Line>());
  [0, 1].forEach(i => view.add(<Line ref={arrows[i]} points={[[xs[i] + 75, 0], [xs[i + 1] - 75, 0]]} stroke={C.fg}
    lineWidth={4} endArrow arrowSize={16} end={0}/>));
  yield* beat('ll1', 0, sequence(0.2, ...nodes.map(n => n().opacity(1, 0.4))));
  yield* beat('ll1', 1, sequence(0.3, ...arrows.map(a => a().end(1, 0.5))));

  const fresh = createRef<Rect>();
  view.add(node(fresh, -250, 230, '5'));
  const link = createRef<Line>();
  view.add(<Line ref={link} points={[[-185, 180], [-105, 55]]} stroke={C.ink} lineWidth={4} endArrow arrowSize={16} end={0}/>);
  yield* beat('ll2', 0, all(fresh().opacity(1, 0.4), fresh().stroke(C.accent, 0.4)));
  yield* beat('ll2', 1, link().end(1, 0.5));
  yield* beat('ll2', 2, all(arrows[0]().points([[-375, 30], [-315, 180]], 0.7), arrows[0]().stroke(C.ink, 0.7)));

  const cost = createRef<Txt>();
  view.add(<Txt ref={cost} y={-260} text="O(1)" fontFamily={C.font} fontWeight={700} fontSize={84} fill={C.ink} opacity={0}/>);
  const more = createRef<Txt>();
  view.add(<Txt ref={more} x={640} text="… a million more" fontFamily={C.font} fontSize={40} fill={C.dim} opacity={0}/>);
  yield* beat('ll3', 0, cost().opacity(1, 0.5));
  yield* beat('ll3', 1, more().opacity(1, 0.5));
  yield* finish();
});
