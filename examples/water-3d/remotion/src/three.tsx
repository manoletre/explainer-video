// 3D in a Remotion explainer, with three.js through @remotion/three (React Three Fiber). Copied from
// the skill's templates/remotion/ by `remotion.py new`. Inside <Scene3D>, write R3F nodes (<mesh>,
// <group>, ...) and animate them from useTime(), like everything else. Call at() outside <Scene3D> and
// pass the times in as props: the 3D renderer draws its children on its own schedule, so the sync check
// can't see at() calls made inside it.
// On a machine without a GPU, Chrome draws WebGL with SwiftShader on the CPU: it works, but each frame
// costs about 10 times a 2D frame, so keep 3D to the beats that need it.
import React from 'react';
import {useThree} from '@react-three/fiber';
import {ThreeCanvas} from '@remotion/three';
import {C, Timed, bump, ramp, useTime} from './kit';
import {useVideoConfig} from 'remotion';

export {useTime};

type Vec3 = [number, number, number];
export type CameraMove = {at: number; dur?: number; position: Vec3; lookAt?: Vec3};

function cameraAt(now: number, start: Vec3, moves: CameraMove[]): {position: Vec3; lookAt: Vec3} {
  let position = start, lookAt: Vec3 = [0, 0, 0];
  for (const mv of [...moves].sort((p, q) => p.at - q.at)) {
    const k = ramp(now, mv.at, mv.dur ?? 1.5);
    if (k <= 0) break;
    position = position.map((v, i) => v + (mv.position[i] - v) * k) as Vec3;
    if (mv.lookAt) lookAt = lookAt.map((v, i) => v + (mv.lookAt![i] - v) * k) as Vec3;
  }
  return {position, lookAt};
}

/** Puts the camera where the moves say it is at this frame. */
const CameraRig: React.FC<{position: Vec3; lookAt: Vec3}> = ({position, lookAt}) => {
  const camera = useThree(st => st.camera);
  camera.position.set(...position);
  camera.lookAt(...lookAt);
  camera.updateProjectionMatrix();
  return null;
};

/** A 3D viewport centered on (x, y), w x h pixels, lit in the theme. `camera` is where it starts,
 *  `moves` fly it elsewhere at narration times. Children are React Three Fiber nodes. */
export const Scene3D: React.FC<Timed & {
  x?: number; y?: number; w?: number; h?: number; camera?: Vec3; fov?: number; moves?: CameraMove[];
  children?: React.ReactNode;
}> = ({x = 960, y = 560, w = 1920, h = 1080, camera = [0, 1.5, 6], fov = 45, moves = [], children, ...t}) => {
  const now = useTime();
  const a = t.at ?? 0;
  const shown = Math.min(ramp(now, a, 0.5), t.out === undefined ? 1 : 1 - ramp(now, t.out, 0.35));
  const {width, height} = useVideoConfig();
  if (shown <= 0.001) return null;
  const cam = cameraAt(now, camera, moves);
  return (
    <div style={{position: 'absolute', left: x - w / 2, top: y - h / 2, width: w, height: h, opacity: shown}}>
      <ThreeCanvas width={Math.min(w, width)} height={Math.min(h, height)} camera={{position: cam.position, fov}}
        gl={{antialias: true}}>
        <CameraRig position={cam.position} lookAt={cam.lookAt}/>
        <ambientLight intensity={C.name === 'light' ? 0.8 : 0.45}/>
        <directionalLight position={[4, 6, 3]} intensity={1.6}/>
        <directionalLight position={[-4, 2, -3]} intensity={0.4}/>
        {children}
      </ThreeCanvas>
    </div>
  );
};

/** Materials in the theme: gold (the accent), the foreground color, or the dim gray; `hot` pulses it brighter. */
export const Gold: React.FC<{hot?: number[]}> = ({hot = []}) => {
  const now = useTime();
  const g = Math.max(0, ...hot.map(h => bump(now, h)));
  return <meshStandardMaterial color={C.accent} metalness={0.35} roughness={0.35} emissive={C.accent} emissiveIntensity={0.35 * g}/>;
};
export const Plain: React.FC<{color?: string; opacity?: number}> = ({color = C.fg, opacity = 1}) =>
  <meshStandardMaterial color={color} roughness={0.6} transparent={opacity < 1} opacity={opacity}/>;

/** Grows from nothing at `at` (spring-free, eased): wrap a mesh or group in it. */
export const Pop: React.FC<{at: number; dur?: number; children?: React.ReactNode}> = ({at, dur = 0.6, children}) => {
  const s = ramp(useTime(), at, dur);
  return <group scale={Math.max(0.0001, s)} visible={s > 0.001}>{children}</group>;
};

