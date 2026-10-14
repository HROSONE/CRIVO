import React, { useMemo } from "react";
import * as THREE from "three";
import { ThreeCanvas } from "@remotion/three";
import { random, useCurrentFrame, useVideoConfig } from "remotion";

const N = 220;
const VIZINHOS = 3;

type Dados = { base: Float32Array; direcao: Float32Array; pares: Uint16Array };

const montar = (): Dados => {
  const base = new Float32Array(N * 3);
  const direcao = new Float32Array(N * 3);
  const ouro = Math.PI * (3 - Math.sqrt(5));
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2;
    const r = Math.sqrt(1 - y * y);
    const t = ouro * i;
    const raio = 2.2 * (0.85 + random(`r${i}`) * 0.3);
    base.set([Math.cos(t) * r * raio, y * raio, Math.sin(t) * r * raio], i * 3);
    // cada nó sai numa direção própria quando a rede é "desmontada"
    const d = new THREE.Vector3(random(`dx${i}`) - 0.5, random(`dy${i}`) - 0.5, random(`dz${i}`) - 0.5)
      .normalize()
      .multiplyScalar(2 + random(`dm${i}`) * 4);
    direcao.set([d.x, d.y, d.z], i * 3);
  }
  const pares: number[] = [];
  for (let i = 0; i < N; i++) {
    const dist: [number, number][] = [];
    for (let j = 0; j < N; j++) {
      if (i === j) continue;
      const dx = base[i * 3] - base[j * 3];
      const dy = base[i * 3 + 1] - base[j * 3 + 1];
      const dz = base[i * 3 + 2] - base[j * 3 + 2];
      dist.push([dx * dx + dy * dy + dz * dz, j]);
    }
    dist.sort((a, b) => a[0] - b[0]);
    for (const [, j] of dist.slice(0, VIZINHOS)) if (i < j) pares.push(i, j);
  }
  return { base, direcao, pares: Uint16Array.from(pares) };
};

/**
 * Rede de nós em esfera (o "cérebro" do CRIVO). `abertura` 0 = montada,
 * 1 = desmontada em pedaços; `pulso` (0..1) vem da energia da voz.
 */
export const Rede3D: React.FC<{
  abertura?: number;
  pulso?: number;
  cor?: string;
  corLinha?: string;
  giro?: number;
  distancia?: number;
  largura?: number;
  altura?: number;
}> = ({ abertura = 0, pulso = 0, cor = "#c6ff3d", corLinha = "#3de0ff", giro = 1, distancia = 7, largura, altura }) => {
  const frame = useCurrentFrame();
  const video = useVideoConfig();
  const width = largura ?? video.width;
  const height = altura ?? video.height;
  const dados = useMemo(montar, []);

  const posicoes = useMemo(() => {
    const p = new Float32Array(N * 3);
    const e = 1 + pulso * 0.08;
    for (let i = 0; i < N * 3; i++) p[i] = dados.base[i] * e + dados.direcao[i] * abertura;
    return p;
  }, [dados, abertura, pulso]);

  const linhas = useMemo(() => {
    const l = new Float32Array(dados.pares.length * 3);
    dados.pares.forEach((idx, k) => l.set(posicoes.subarray(idx * 3, idx * 3 + 3), k * 3));
    return l;
  }, [dados, posicoes]);

  const rot = frame * 0.006 * giro;
  return (
    <ThreeCanvas width={width} height={height} camera={{ position: [0, 0, distancia], fov: 45 }}>
      <ambientLight intensity={0.6} />
      <pointLight position={[5, 5, 5]} intensity={40} color={cor} />
      <pointLight position={[-5, -3, 2]} intensity={25} color={corLinha} />
      <group rotation={[0.3 + Math.sin(frame / 90) * 0.15, rot, 0]}>
        <points key={`p${frame}`}>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[posicoes, 3]} />
          </bufferGeometry>
          <pointsMaterial color={cor} size={0.09 + pulso * 0.05} sizeAttenuation />
        </points>
        <lineSegments key={`l${frame}`}>
          <bufferGeometry>
            <bufferAttribute attach="attributes-position" args={[linhas, 3]} />
          </bufferGeometry>
          <lineBasicMaterial color={corLinha} transparent opacity={0.35 * (1 - abertura * 0.6)} />
        </lineSegments>
        <mesh rotation={[rot * 2, rot * 1.3, 0]} scale={0.9 + pulso * 0.25}>
          <icosahedronGeometry args={[1, 1]} />
          <meshStandardMaterial color={cor} wireframe emissive={cor} emissiveIntensity={0.4 + pulso} />
        </mesh>
      </group>
    </ThreeCanvas>
  );
};
