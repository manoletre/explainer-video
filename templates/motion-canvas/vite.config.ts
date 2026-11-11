import {defineConfig} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';

const plugin = (motionCanvas as any).default ?? motionCanvas;
export default defineConfig({plugins: [plugin()]});
