import { useEffect, useState } from "react";
import { staticFile, useDelayRender } from "remotion";

/** Carrega um JSON de public/ segurando a renderização até chegar. */
export const useJson = <T,>(arquivo: string): T | null => {
  const [dados, setDados] = useState<T | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender(`carregando ${arquivo}`));
  useEffect(() => {
    fetch(staticFile(arquivo))
      .then((r) => r.json())
      .then((d) => {
        setDados(d);
        continueRender(handle);
      })
      .catch(cancelRender);
  }, [arquivo, handle, continueRender, cancelRender]);
  return dados;
};
