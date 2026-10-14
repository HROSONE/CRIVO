import React from "react";
import * as THREE from "three";
import { ThreeCanvas } from "@remotion/three";
import { useVideoConfig } from "remotion";

export const CAMADAS = [
  { nome: "interface", cor: "#3de0ff" },
  { nome: "comportamento", cor: "#c6ff3d" },
  { nome: "lógica e regras", cor: "#ffb02e" },
  { nome: "dados e APIs", cor: "#ff4fa3" },
  { nome: "binário", cor: "#a77bff" },
];

const POS_CAMERA = new THREE.Vector3(7, 5.5, 9);

/**
 * App visto em "vista explodida": camadas empilhadas que se separam
 * (`abertura` 0..1) e um plano de varredura (`varre` 0..1) que as atravessa.
 * `visiveis` limita quantas camadas aparecem (de cima para baixo).
 */
export const Camadas3D: React.FC<{
  abertura: number;
  varre: number;
  visiveis: number;
  giro: number;
}> = ({ abertura, varre, visiveis, giro }) => {
  const { width, height } = useVideoConfig();
  const alturas = CAMADAS.map((_, i) => (2 - i) * (0.25 + abertura * 0.95));
  const yVarre = THREE.MathUtils.lerp(alturas[0] + 0.6, alturas[CAMADAS.length - 1] - 0.6, varre);
  return (
    <ThreeCanvas
      width={width}
      height={height}
      camera={{ position: POS_CAMERA.toArray() as [number, number, number], fov: 38 }}
      onCreated={({ camera }) => camera.lookAt(0, 0, 0)}
    >
      <ambientLight intensity={0.6} />
      <directionalLight position={[4, 8, 6]} intensity={1.5} />
      <group rotation={[0, giro, 0]}>
        {CAMADAS.map((c, i) => (
          <group key={c.nome} position={[0, alturas[i], 0]} visible={i < visiveis}>
            <mesh>
              <boxGeometry args={[4.2, 0.08, 2.8]} />
              <meshStandardMaterial color={c.cor} transparent opacity={0.28} emissive={c.cor} emissiveIntensity={0.25} />
            </mesh>
            <lineSegments>
              <edgesGeometry args={[new THREE.BoxGeometry(4.2, 0.08, 2.8)]} />
              <lineBasicMaterial color={c.cor} />
            </lineSegments>
            {/* "componentes" dentro da camada */}
            {Array.from({ length: 6 }, (_, k) => (
              <mesh key={k} position={[-1.5 + (k % 3) * 1.5, 0.08, -0.7 + Math.floor(k / 3) * 1.4]}>
                <boxGeometry args={[1.1, 0.06 + ((k * 7 + i * 3) % 5) * 0.04, 0.9]} />
                <meshStandardMaterial color={c.cor} emissive={c.cor} emissiveIntensity={0.15} />
              </mesh>
            ))}
          </group>
        ))}
        <mesh position={[0, yVarre, 0]} visible={varre > 0 && varre < 1}>
          <boxGeometry args={[5.2, 0.02, 3.6]} />
          <meshBasicMaterial color="#ffffff" transparent opacity={0.55} />
        </mesh>
      </group>
    </ThreeCanvas>
  );
};

/** Posição na tela (px) do centro de cada camada, para os rótulos em HTML. */
export const projetarCamadas = (abertura: number, giro: number, width: number, height: number) => {
  const cam = new THREE.PerspectiveCamera(38, width / height, 0.1, 100);
  cam.position.copy(POS_CAMERA);
  cam.lookAt(0, 0, 0);
  cam.updateMatrixWorld();
  return CAMADAS.map((_, i) => {
    const v = new THREE.Vector3(2.1, (2 - i) * (0.25 + abertura * 0.95), 0).applyAxisAngle(
      new THREE.Vector3(0, 1, 0),
      giro,
    );
    v.project(cam);
    return { x: ((v.x + 1) / 2) * width, y: ((1 - v.y) / 2) * height };
  });
};
