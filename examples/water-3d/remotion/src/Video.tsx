import React from 'react';
import {C, Section, Text, at} from './kit';
import {Gold, Plain, Pop, Scene3D} from './three';

const ANGLE = (104.5 / 2) * (Math.PI / 180);
const BOND = 1.5;
const H: [number, number][] = [[Math.sin(ANGLE) * BOND, -Math.cos(ANGLE) * BOND], [-Math.sin(ANGLE) * BOND, -Math.cos(ANGLE) * BOND]];

// at() is read outside <Scene3D> and passed in: the 3D renderer draws its children on its own schedule
const Molecule: React.FC<{o: number; h: number}> = ({o, h}) => <>
  <Pop at={o}>
    <mesh><sphereGeometry args={[0.62, 48, 48]}/><Gold hot={[o + 0.6]}/></mesh>
  </Pop>
  {H.map(([x, y], i) => (
    <Pop key={i} at={h + i * 0.3}>
      <mesh position={[x, y, 0]}><sphereGeometry args={[0.36, 48, 48]}/><Plain/></mesh>
      <mesh position={[x / 2, y / 2, 0]} rotation={[0, 0, i === 0 ? ANGLE : -ANGLE]}>
        <cylinderGeometry args={[0.1, 0.1, BOND, 24]}/><Plain color={C.dim}/>
      </mesh>
    </Pop>
  ))}
</>;

export const Scenes: React.FC = () => <>
  <Section id="wa1">
    <Scene3D at={at('wa1', 0)} camera={[0, 0.2, 6]} moves={[{at: at('wa3', 0), dur: 2.2, position: [6, 0.2, 0.01]}]}>
      <group position={[0, 0.4, 0]}><Molecule o={at('wa1', 1)} h={at('wa1', 2)}/></group>
    </Scene3D>
    <Text x={960} y={170} size={60} weight={700} at={at('wa1', 0)}>H₂O</Text>
    <Text x={960} y={1000} size={40} at={at('wa2', 0)} out={at('wa3', 0)} hot={[at('wa2', 0) + 0.5]}>bond angle ≈ 104.5°</Text>
    <Text x={960} y={1000} size={40} at={at('wa3', 1)} hot={[at('wa3', 2)]}>flat: all three atoms in one plane</Text>
    <Text x={1500} y={560} size={44} color={C.ink} at={at('wa2', 1)} out={at('wa3', 0)}>bent, not straight</Text>
  </Section>
</>;
