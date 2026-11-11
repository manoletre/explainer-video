import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {Explainer, TL} from './kit';
import {Scenes} from './Video';

const Main: React.FC = () => <Explainer><Scenes/></Explainer>;

const Root: React.FC = () => (
  <Composition id="Explainer" component={Main} fps={TL.fps} width={TL.width} height={TL.height}
    durationInFrames={Math.max(1, Math.ceil(TL.duration * TL.fps))}/>
);

registerRoot(Root);
