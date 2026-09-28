import { Loader2 } from "lucide-react";

/** Sayfa ilk yuklenirken (oturum/kullanici verisi gelene kadar) beyaz/bos
 * ekran yerine gosterilen tam ekran yukleniyor gostergesi. */
export default function PageLoader() {
  return (
    <main className="min-h-screen bg-black flex items-center justify-center">
      <Loader2 className="h-6 w-6 text-zinc-600 animate-spin" />
    </main>
  );
}
