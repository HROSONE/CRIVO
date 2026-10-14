import React, { useCallback, useMemo } from "react";
import * as THREE from "three";
import { ThreeCanvas } from "@remotion/three";
import { interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";

const LADO = 24;
const MAX = LADO * LADO;
const CORES = ["#c6ff3d", "#3de0ff", "#ffb02e", "#ff4fa3", "#a77bff", "#2fd07a"];

/**
 * Parede de "apps" em 3D: um único app vira 4, 16, 64… até centenas de cópias,
 * cada uma nascendo com um estalo. `quantos` vai de 1 a MAX.
 */
export const GradeClones3D: React.FC<{ quantos: number; recuo: number }> = ({ quantos, recuo }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // ordem de nascimento: do centro para fora
  const ordem = useMemo(() => {
    const idx = Array.from({ length: MAX }, (_, i) => i);
    const c = (LADO - 1) / 2;
    return idx.sort((a, b) => {
      const da = Math.hypot((a % LADO) - c, Math.floor(a / LADO) - c) + random(`o${a}`) * 0.8;
      const db = Math.hypot((b % LADO) - c, Math.floor(b / LADO) - c) + random(`o${b}`) * 0.8;
      return da - db;
    });
  }, []);

  // ref de callback: o R3F monta a malha depois dos efeitos do React,
  // então as matrizes são aplicadas quando ela é anexada (a cada quadro).
  const aplicar = useCallback((m: THREE.InstancedMesh | null) => {
    if (!m) return;
    const tmp = new THREE.Object3D();
    const cor = new THREE.Color();
    const c = (LADO - 1) / 2;
    for (let k = 0; k < MAX; k++) {
      const i = ordem[k];
      const idade = quantos - k; // >0: já nasceu
      const s = k < quantos ? Math.min(1, idade / 6) : 0;
      const x = (i % LADO) - c;
      const y = Math.floor(i / LADO) - c;
      tmp.position.set(x * 1.25, y * 0.95, Math.sin(x * 0.7 + frame / 20) * 0.15 * s);
      tmp.rotation.set(0, 0, 0);
      tmp.scale.setScalar(s);
      tmp.updateMatrix();
      m.setMatrixAt(k, tmp.matrix);
      m.setColorAt(k, cor.set(k === 0 ? "#f2f4f8" : CORES[i % CORES.length]));
    }
    m.instanceMatrix.needsUpdate = true;
    if (m.instanceColor) m.instanceColor.needsUpdate = true;
    m.computeBoundingSphere();
  }, [quantos, ordem, frame]);

  const giro = interpolate(frame, [0, 100], [0.25, -0.15]);
  return (
    <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, recuo], fov: 40 }}>
      <ambientLight intensity={0.7} />
      <directionalLight position={[3, 4, 8]} intensity={1.6} />
      <group rotation={[-0.35, giro, 0.05]}>
        <instancedMesh ref={aplicar} args={[undefined, undefined, MAX]} frustumCulled={false}>
          <boxGeometry args={[1, 0.72, 0.12]} />
          <meshStandardMaterial roughness={0.4} metalness={0.1} />
        </instancedMesh>
      </group>
    </ThreeCanvas>
  );
};
