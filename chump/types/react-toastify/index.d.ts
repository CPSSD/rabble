interface IToastPosition {
    BOTTOM_RIGHT: number;
}

interface IToastConfiguration {
    autoClose: number;
    draggable: boolean;
    position: number;
}

interface IToast {
    configure(c: IToastConfiguration): void;
    error(m: string): void;
    success(m: string): void;
    POSITION: IToastPosition;
}

declare module 'react-toastify' {
    export const toast: IToast
}
