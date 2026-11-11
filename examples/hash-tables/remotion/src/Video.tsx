import React from 'react';
import {Arrow, Box, C, Formula, Plot, Pointer, Section, Text, at} from './kit';

const NAMES = ['Lin', 'Grace', 'Alan', 'Barbara', 'Edsger', 'Ada', 'Ken', '…'];
const listY = (i: number) => 230 + i * 92;
const bucketX = (i: number) => 160 + i * 140;

const Problem: React.FC = () => {
  const scan = at('pr1', 2);
  return <>
    {NAMES.map((n, i) => (
      <Box key={n} x={520} y={listY(i)} w={260} h={74} size={32} title={n} at={at('pr1', 0) + i * 0.08}
        hot={i < 7 ? [scan + i * 0.45] : []}/>
    ))}
    <Text x={520} y={970} size={30} color={C.dim} at={at('pr1', 0) + 0.7}>a million names, in no order</Text>
    <Box x={1300} y={260} w={260} h={96} title="Ada?" color={C.accent} at={at('pr1', 1)}/>
    <Pointer moves={[
      ...NAMES.slice(0, 6).map((_, i) => ({at: scan + i * 0.45, x: 680, y: listY(i)})),
      {at: at('pr2', 0), hide: true},
    ]}/>
    <Text x={1300} y={480} size={54} at={at('pr2', 0)}>≈ 500,000 comparisons</Text>
    <Text x={1300} y={570} size={36} color={C.dim} at={at('pr2', 1)}>1,000,000 when Ada isn’t there</Text>
    <Text x={1300} y={720} size={60} weight={700} color={C.ink} at={at('pr2', 2)} hot={[at('pr2', 2) + 0.4]}>
      hash table: about 1
    </Text>
  </>;
};

const Buckets: React.FC<{y: number; at: number; hot?: Record<number, number[]>; dim?: number}> = ({y, at: t, hot = {}, dim}) => <>
  {Array.from({length: 8}, (_, i) => (
    <Box key={i} x={bucketX(i)} y={y} w={110} h={90} title={String(i)} size={36} at={t + i * 0.06}
      hot={hot[i]} dim={dim}/>
  ))}
</>;

const Trick: React.FC = () => <>
  <Box x={960} y={360} w={340} h={120} title="hash( )" size={44} at={at('hf1', 0)} hot={[at('hf2', 0)]}/>
  <Box x={400} y={360} w={220} h={100} title="“Ada”" size={40} at={at('hf1', 1)}/>
  <Arrow from={[515, 360]} to={[785, 360]} at={at('hf1', 1) + 0.3}/>
  <Arrow from={[1135, 360]} to={[1330, 360]} at={at('hf1', 2)}/>
  <Text x={1560} y={360} size={48} mono at={at('hf1', 2)}>1,702,387</Text>
  <Formula x={1560} y={500} size={50} tex={'1702387 \\bmod 8 = 3'} at={at('hf1', 3)}/>
  <Buckets y={800} at={at('hf1', 3)} hot={{3: [at('hf1', 3) + 0.6, at('hf2', 1) + 0.5]}}/>
  <Arrow from={[1450, 560]} to={[bucketX(3) + 40, 745]} bend={-0.15} at={at('hf2', 1)} color={C.ink}/>
  <Box x={bucketX(3)} y={950} w={150} h={70} size={30} title="Ada" at={at('hf2', 2)} hot={[at('hf2', 2) + 0.5]}/>
  <Pointer moves={[{at: at('hf2', 1) + 0.2, x: bucketX(3), y: 800, ring: 70}, {at: at('hf2', 2) + 0.3, x: bucketX(3) + 95, y: 950}]}/>
</>;

const Collisions: React.FC = () => {
  const alpha = (a: number) => 1 + a / 2;
  return <>
    <Buckets y={330} at={at('co1', 0)} dim={at('co3', 1)} hot={{5: [at('co1', 1)]}}/>
    <Box x={780} y={170} w={130} h={70} size={30} title="Ada" at={at('co1', 0) + 0.3}/>
    <Box x={980} y={170} w={130} h={70} size={30} title="Bob" at={at('co1', 0) + 0.6}/>
    <Arrow from={[800, 207]} to={[bucketX(5) - 15, 282]} at={at('co1', 0) + 0.5} color={C.ink}/>
    <Arrow from={[960, 207]} to={[bucketX(5) + 15, 282]} at={at('co1', 0) + 0.8} color={C.ink}/>
    <Box x={bucketX(5)} y={480} w={150} h={76} size={30} title="Ada" at={at('co1', 2)}/>
    <Box x={bucketX(5)} y={600} w={150} h={76} size={30} title="Bob" at={at('co1', 2) + 0.4}/>
    <Arrow from={[bucketX(5), 377]} to={[bucketX(5), 438]} at={at('co1', 2)}/>
    <Arrow from={[bucketX(5), 520]} to={[bucketX(5), 558]} at={at('co1', 2) + 0.4}/>
    <Formula x={1580} y={300} size={58} tex={'\\alpha = \\frac{n}{m}'} at={at('co2', 0)} hot={[at('co3', 0)]}/>
    <Text x={1580} y={385} size={28} color={C.dim} at={at('co2', 1)}>keys over buckets</Text>
    <Pointer moves={[{at: at('co2', 1), x: 1650, y: 272}, {at: at('co2', 2), x: 1650, y: 334},
      {at: at('co2', 3), hide: true}]}/>
    <Formula x={1580} y={490} size={50} tex={'\\text{checks} \\approx 1 + \\frac{\\alpha}{2}'} at={at('co2', 3)}/>
    <Plot x={1580} y={790} w={500} h={260} xr={[0, 2]} yr={[0, 2.2]} xlabel="α" ylabel="checks" at={at('co3', 0)}
      series={[{f: alpha, at: at('co3', 0), dur: 1.6}]}/>
    <Text x={600} y={820} size={40} at={at('co3', 1)}>full? double the buckets: 8 → 16</Text>
    <Text x={600} y={920} size={34} color={C.dim} at={at('co3', 3)}>a thousand keys or a billion: still about 1.4 checks</Text>
    <Pointer moves={[{at: at('co3', 2), x: 1330 + 250 * 0.75, y: 920 - 260 * alpha(0.75) / 2.2, ring: 34},
      {at: at('co3', 3) + 1.5, hide: true}]}/>
  </>;
};

const Summary: React.FC = () => <>
  <Text x={960} y={260} size={56} weight={700} at={at('su1', 0)}>a hash table</Text>
  <Box x={560} y={480} w={520} h={200} title="extra memory" sub="an array of buckets, some empty" size={46}
    at={at('su1', 1)}/>
  <Arrow from={[830, 480]} to={[1080, 480]} at={at('su1', 2)}/>
  <Box x={1360} y={480} w={520} h={200} title="O(1) lookups" size={46} at={at('su1', 2)} hot={[at('su1', 3)]}/>
  <Text x={1360} y={640} size={36} color={C.dim} at={at('su1', 3)}>on average</Text>
  <Text x={960} y={820} size={44} at={at('su1', 4)} hot={[at('su1', 4) + 0.5]}>
    use it for exact keys, looked up many times
  </Text>
</>;

export const Scenes: React.FC = () => <>
  <Section id="pr1"><Problem/></Section>
  <Section id="hf1"><Trick/></Section>
  <Section id="co1"><Collisions/></Section>
  <Section id="su1"><Summary/></Section>
</>;
